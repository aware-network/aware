# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "attention-service-api"
API_FQN_PREFIX: Final[str] = "aware_attention_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Activate one ontology-backed "
                                "observable for one section-scoped "
                                "Attention focus scope.",
                                "discriminant": "attention.activate_section_observable.activate_section_observable",
                                "name": "activate_section_observable",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.ActivateAttentionSectionObservableRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.ActivateAttentionSectionObservableResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "activate_section_observable",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Atomically commit one complete "
                                "active-membership/order vector on an "
                                "AttentionSession lane.",
                                "discriminant": "attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition",
                                "name": "apply_session_layout_topology_transition",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTopologyTransitionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTopologyTransitionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "apply_session_layout_topology_transition",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Atomically commit one complete typed "
                                "shared-layout vector on an "
                                "AttentionSession lane.",
                                "discriminant": "attention.apply_session_layout_transition.apply_session_layout_transition",
                                "name": "apply_session_layout_transition",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTransitionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTransitionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "apply_session_layout_transition",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read one AttentionSession and its "
                                "active layout/section/transition pins.",
                                "discriminant": "attention.describe_attention_session.describe_attention_session",
                                "name": "describe_attention_session",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.DescribeAttentionSessionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.DescribeAttentionSessionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "describe_attention_session",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read one AttentionFocusTransition pin "
                                "plus its parent session chain.",
                                "discriminant": "attention.describe_attention_transition.describe_attention_transition",
                                "name": "describe_attention_transition",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.DescribeAttentionTransitionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.DescribeAttentionTransitionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "describe_attention_transition",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List committed OIG commit pointers "
                                "observed by one Attention focus scope.",
                                "discriminant": "attention.get_focus_scope_commits.get_focus_scope_commits",
                                "name": "get_focus_scope_commits",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionFocusScopeCommitsRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionFocusScopeCommitsResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "get_focus_scope_commits",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read one typed batch snapshot of "
                                "Attention-owned section state for the "
                                "currently mounted\n"
                                "            bundle-backed runtime "
                                "layout, optionally seeding section "
                                "defaults supplied by Interface.",
                                "discriminant": "attention.get_runtime_mount.get_runtime_mount",
                                "name": "get_runtime_mount",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionRuntimeMountRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionRuntimeMountResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "get_runtime_mount",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the current section-scoped "
                                "focus-scope and observable state for "
                                "one Attention section,\n"
                                "            optionally seeding a "
                                "missing observable from an "
                                "Interface-supplied default candidate.",
                                "discriminant": "attention.get_section_state.get_section_state",
                                "name": "get_section_state",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionSectionStateRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionSectionStateResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "get_section_state",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List AttentionFocusTransition pins by "
                                "session, section, focus-scope, or "
                                "kind.",
                                "discriminant": "attention.list_attention_transitions.list_attention_transitions",
                                "name": "list_attention_transitions",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ListAttentionTransitionsRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ListAttentionTransitionsResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "list_attention_transitions",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Mount one Attention Layout on an "
                                "existing committed AttentionSession "
                                "lane.",
                                "discriminant": "attention.mount_attention_session_layout.mount_attention_session_layout",
                                "name": "mount_attention_session_layout",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.MountAttentionSessionLayoutRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.MountAttentionSessionLayoutResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "mount_attention_session_layout",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Mount one Attention Section anchor on "
                                "an existing committed session layout.",
                                "discriminant": "attention.mount_attention_session_section.mount_attention_session_section",
                                "name": "mount_attention_session_section",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.MountAttentionSessionSectionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.MountAttentionSessionSectionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "mount_attention_session_section",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Construct one commit-backed "
                                "AttentionSession over a verified "
                                "Identity Session.",
                                "discriminant": "attention.start_attention_session.start_attention_session",
                                "name": "start_attention_session",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.StartAttentionSessionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.StartAttentionSessionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "start_attention_session",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Validate that one "
                                "AttentionFocusTransition matches "
                                "expected Attention session "
                                "coordinates.",
                                "discriminant": "attention.validate_attention_transition.validate_attention_transition",
                                "name": "validate_attention_transition",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ValidateAttentionTransitionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ValidateAttentionTransitionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "validate_attention_transition",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Subscribe to streamed Attention "
                                "runtime-mount snapshots for the "
                                "currently mounted\n"
                                "            bundle-backed layout "
                                "candidates.",
                                "discriminant": "attention.watch_runtime_mount.watch_runtime_mount",
                                "name": "watch_runtime_mount",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.WatchAttentionRuntimeMountRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.WatchAttentionRuntimeMountResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed "
                                    "runtime-mount snapshots "
                                    "emitted by the Attention "
                                    "service boundary.",
                                    "events": [
                                        {
                                            "class_ref": "aware_attention_service_dto.attention.section.AttentionRuntimeMountSnapshotEvent",
                                            "kind": "snapshot",
                                            "source_path": "bindings/attention.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/attention.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_runtime_mount",
                        "source_path": "bindings/attention.apis.aware",
                    },
                ],
                "name": "attention",
                "source_path": "bindings/attention.apis.aware",
            }
        ],
        "fqn_prefix": "aware_attention_service_api",
        "package_name": "attention-service-api",
        "schema_version": 1,
    }
)

API_INVOCATION_MANIFEST: Final[LoadedApiInvocationManifest] = load_api_invocation_manifest_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Activate one ontology-backed "
                                "observable for one section-scoped "
                                "Attention focus scope.",
                                "discriminant": "attention.activate_section_observable.activate_section_observable",
                                "endpoint_ref": "attention.activate_section_observable.activate_section_observable",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "activate_section_observable",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.ActivateAttentionSectionObservableRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.ActivateAttentionSectionObservableRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.ActivateAttentionSectionObservableResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.ActivateAttentionSectionObservableResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "activate_section_observable",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Atomically commit one complete "
                                "active-membership/order vector on an "
                                "AttentionSession lane.",
                                "discriminant": "attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition",
                                "endpoint_ref": "attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "apply_session_layout_topology_transition",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTopologyTransitionRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.ApplyAttentionSessionLayoutTopologyTransitionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTopologyTransitionResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.ApplyAttentionSessionLayoutTopologyTransitionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "apply_session_layout_topology_transition",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Atomically commit one complete typed "
                                "shared-layout vector on an "
                                "AttentionSession lane.",
                                "discriminant": "attention.apply_session_layout_transition.apply_session_layout_transition",
                                "endpoint_ref": "attention.apply_session_layout_transition.apply_session_layout_transition",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "apply_session_layout_transition",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTransitionRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.ApplyAttentionSessionLayoutTransitionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTransitionResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.ApplyAttentionSessionLayoutTransitionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "apply_session_layout_transition",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read one AttentionSession and its "
                                "active layout/section/transition pins.",
                                "discriminant": "attention.describe_attention_session.describe_attention_session",
                                "endpoint_ref": "attention.describe_attention_session.describe_attention_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_attention_session",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.DescribeAttentionSessionRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.DescribeAttentionSessionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.DescribeAttentionSessionResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.DescribeAttentionSessionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "describe_attention_session",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read one AttentionFocusTransition pin "
                                "plus its parent session chain.",
                                "discriminant": "attention.describe_attention_transition.describe_attention_transition",
                                "endpoint_ref": "attention.describe_attention_transition.describe_attention_transition",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_attention_transition",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.DescribeAttentionTransitionRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.DescribeAttentionTransitionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.DescribeAttentionTransitionResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.DescribeAttentionTransitionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "describe_attention_transition",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List committed OIG commit pointers "
                                "observed by one Attention focus scope.",
                                "discriminant": "attention.get_focus_scope_commits.get_focus_scope_commits",
                                "endpoint_ref": "attention.get_focus_scope_commits.get_focus_scope_commits",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_focus_scope_commits",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionFocusScopeCommitsRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.GetAttentionFocusScopeCommitsRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionFocusScopeCommitsResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.GetAttentionFocusScopeCommitsResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "get_focus_scope_commits",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read one typed batch snapshot of "
                                "Attention-owned section state for the "
                                "currently mounted\n"
                                "            bundle-backed runtime "
                                "layout, optionally seeding section "
                                "defaults supplied by Interface.",
                                "discriminant": "attention.get_runtime_mount.get_runtime_mount",
                                "endpoint_ref": "attention.get_runtime_mount.get_runtime_mount",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_runtime_mount",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionRuntimeMountRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.GetAttentionRuntimeMountRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionRuntimeMountResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.GetAttentionRuntimeMountResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "get_runtime_mount",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the current section-scoped "
                                "focus-scope and observable state for "
                                "one Attention section,\n"
                                "            optionally seeding a "
                                "missing observable from an "
                                "Interface-supplied default candidate.",
                                "discriminant": "attention.get_section_state.get_section_state",
                                "endpoint_ref": "attention.get_section_state.get_section_state",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_section_state",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionSectionStateRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.GetAttentionSectionStateRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.GetAttentionSectionStateResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.GetAttentionSectionStateResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "get_section_state",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List AttentionFocusTransition pins by "
                                "session, section, focus-scope, or "
                                "kind.",
                                "discriminant": "attention.list_attention_transitions.list_attention_transitions",
                                "endpoint_ref": "attention.list_attention_transitions.list_attention_transitions",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list_attention_transitions",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ListAttentionTransitionsRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.ListAttentionTransitionsRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ListAttentionTransitionsResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.ListAttentionTransitionsResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "list_attention_transitions",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Mount one Attention Layout on an "
                                "existing committed AttentionSession "
                                "lane.",
                                "discriminant": "attention.mount_attention_session_layout.mount_attention_session_layout",
                                "endpoint_ref": "attention.mount_attention_session_layout.mount_attention_session_layout",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "mount_attention_session_layout",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.MountAttentionSessionLayoutRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.MountAttentionSessionLayoutRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.MountAttentionSessionLayoutResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.MountAttentionSessionLayoutResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "mount_attention_session_layout",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Mount one Attention Section anchor on "
                                "an existing committed session layout.",
                                "discriminant": "attention.mount_attention_session_section.mount_attention_session_section",
                                "endpoint_ref": "attention.mount_attention_session_section.mount_attention_session_section",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "mount_attention_session_section",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.MountAttentionSessionSectionRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.MountAttentionSessionSectionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.MountAttentionSessionSectionResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.MountAttentionSessionSectionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "mount_attention_session_section",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Construct one commit-backed "
                                "AttentionSession over a verified "
                                "Identity Session.",
                                "discriminant": "attention.start_attention_session.start_attention_session",
                                "endpoint_ref": "attention.start_attention_session.start_attention_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "start_attention_session",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.StartAttentionSessionRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.StartAttentionSessionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.StartAttentionSessionResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.StartAttentionSessionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "start_attention_session",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate that one "
                                "AttentionFocusTransition matches "
                                "expected Attention session "
                                "coordinates.",
                                "discriminant": "attention.validate_attention_transition.validate_attention_transition",
                                "endpoint_ref": "attention.validate_attention_transition.validate_attention_transition",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "validate_attention_transition",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ValidateAttentionTransitionRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.ValidateAttentionTransitionRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.session.ValidateAttentionTransitionResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.session.service_operation.ValidateAttentionTransitionResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                            }
                        ],
                        "name": "validate_attention_transition",
                        "source_path": "bindings/attention.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Subscribe to streamed Attention "
                                "runtime-mount snapshots for the "
                                "currently mounted\n"
                                "            bundle-backed layout "
                                "candidates.",
                                "discriminant": "attention.watch_runtime_mount.watch_runtime_mount",
                                "endpoint_ref": "attention.watch_runtime_mount.watch_runtime_mount",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "watch_runtime_mount",
                                "request": {
                                    "class_ref": "aware_attention_service_dto.attention.section.WatchAttentionRuntimeMountRequest",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.WatchAttentionRuntimeMountRequest",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_attention_service_dto.attention.section.WatchAttentionRuntimeMountResponse",
                                    "python_model_ref": "aware_attention_service_dto.attention.section.service_operation.WatchAttentionRuntimeMountResponse",
                                    "source_path": "bindings/attention.apis.aware",
                                },
                                "source_path": "bindings/attention.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed "
                                    "runtime-mount snapshots "
                                    "emitted by the Attention "
                                    "service boundary.",
                                    "events": [
                                        {
                                            "class_ref": "aware_attention_service_dto.attention.section.AttentionRuntimeMountSnapshotEvent",
                                            "kind": "snapshot",
                                            "python_model_ref": "aware_attention_service_dto.attention.section.models.AttentionRuntimeMountSnapshotEvent",
                                            "source_path": "bindings/attention.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/attention.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_runtime_mount",
                        "source_path": "bindings/attention.apis.aware",
                    },
                ],
                "name": "attention",
                "source_path": "bindings/attention.apis.aware",
            }
        ],
        "fqn_prefix": "aware_attention_service_api",
        "package_name": "attention-service-api",
        "schema_version": 1,
    }
)

ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_ENDPOINT_REF: Final[str] = (
    "attention.activate_section_observable.activate_section_observable"
)
ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF: Final[
    str
] = "attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition"
ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_ENDPOINT_REF: Final[str] = (
    "attention.apply_session_layout_transition.apply_session_layout_transition"
)
ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_ENDPOINT_REF: Final[str] = (
    "attention.describe_attention_session.describe_attention_session"
)
ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_ENDPOINT_REF: Final[str] = (
    "attention.describe_attention_transition.describe_attention_transition"
)
ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_ENDPOINT_REF: Final[str] = (
    "attention.get_focus_scope_commits.get_focus_scope_commits"
)
ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_ENDPOINT_REF: Final[str] = (
    "attention.get_runtime_mount.get_runtime_mount"
)
ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_ENDPOINT_REF: Final[str] = (
    "attention.get_section_state.get_section_state"
)
ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_ENDPOINT_REF: Final[str] = (
    "attention.list_attention_transitions.list_attention_transitions"
)
ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_ENDPOINT_REF: Final[str] = (
    "attention.mount_attention_session_layout.mount_attention_session_layout"
)
ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_ENDPOINT_REF: Final[str] = (
    "attention.mount_attention_session_section.mount_attention_session_section"
)
ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_ENDPOINT_REF: Final[str] = (
    "attention.start_attention_session.start_attention_session"
)
ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_ENDPOINT_REF: Final[str] = (
    "attention.validate_attention_transition.validate_attention_transition"
)
ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF: Final[str] = (
    "attention.watch_runtime_mount.watch_runtime_mount"
)

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "attention.activate_section_observable.activate_section_observable": ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_ENDPOINT_REF,
    "attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition": ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF,
    "attention.apply_session_layout_transition.apply_session_layout_transition": ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_ENDPOINT_REF,
    "attention.describe_attention_session.describe_attention_session": ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_ENDPOINT_REF,
    "attention.describe_attention_transition.describe_attention_transition": ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_ENDPOINT_REF,
    "attention.get_focus_scope_commits.get_focus_scope_commits": ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_ENDPOINT_REF,
    "attention.get_runtime_mount.get_runtime_mount": ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_ENDPOINT_REF,
    "attention.get_section_state.get_section_state": ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_ENDPOINT_REF,
    "attention.list_attention_transitions.list_attention_transitions": ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_ENDPOINT_REF,
    "attention.mount_attention_session_layout.mount_attention_session_layout": ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_ENDPOINT_REF,
    "attention.mount_attention_session_section.mount_attention_session_section": ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_ENDPOINT_REF,
    "attention.start_attention_session.start_attention_session": ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_ENDPOINT_REF,
    "attention.validate_attention_transition.validate_attention_transition": ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_ENDPOINT_REF,
    "attention.watch_runtime_mount.watch_runtime_mount": ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_ENDPOINT_REF",
    "ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF",
    "ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_ENDPOINT_REF",
    "ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_ENDPOINT_REF",
    "ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_ENDPOINT_REF",
    "ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_ENDPOINT_REF",
    "ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_ENDPOINT_REF",
    "ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_ENDPOINT_REF",
    "ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_ENDPOINT_REF",
    "ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_ENDPOINT_REF",
    "ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_ENDPOINT_REF",
    "ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_ENDPOINT_REF",
    "ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_ENDPOINT_REF",
    "ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF",
]
