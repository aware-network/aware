# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "interface-service-api"
API_FQN_PREFIX: Final[str] = "aware_interface_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Activate an Interface runtime section "
                                "representation or focus target.",
                                "discriminant": "interface.activate_interface_runtime_focus.activate_interface_runtime_focus",
                                "name": "activate_interface_runtime_focus",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "activate_interface_runtime_focus",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Admit the current Interface actor to "
                                "an Environment/Profile before "
                                "Experience lens resolution.",
                                "discriminant": "interface.admit_environment_actor.admit_environment_actor",
                                "name": "admit_environment_actor",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "admit_environment_actor",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Admit or resume one renderer/agent "
                                "namespace into the Interface service "
                                "runtime.",
                                "discriminant": "interface.admit_interface.admit_interface",
                                "name": "admit_interface",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.NamespaceEnsureRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.NamespaceEnsureResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "admit_interface",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Commit one complete "
                                "active-membership/order vector through "
                                "Interface Host and Attention "
                                "authority.",
                                "discriminant": "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition",
                                "name": "apply_attention_layout_topology_transition",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "apply_attention_layout_topology_transition",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Commit one complete shared-layout "
                                "vector through Interface Host and "
                                "Attention authority.",
                                "discriminant": "interface.apply_attention_layout_transition.apply_attention_layout_transition",
                                "name": "apply_attention_layout_transition",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "apply_attention_layout_transition",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read one committed InterfaceSession "
                                "and its Interface-owned "
                                "ExperienceSession portal rows.",
                                "discriminant": "interface.describe_interface_session.describe_interface_session",
                                "name": "describe_interface_session",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionDescribeRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionDescribeResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "describe_interface_session",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Enter one committed AppPackage screen "
                                "through Interface Host and Experience "
                                "layout activation.",
                                "discriminant": "interface.enter_app_screen.enter_app_screen",
                                "name": "enter_app_screen",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterAppScreenRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterAppScreenResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "enter_app_screen",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Enter or resume an Environment shell "
                                "context without Interface-owned "
                                "Process/Thread defaults.",
                                "discriminant": "interface.enter_environment.enter_environment",
                                "name": "enter_environment",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "enter_environment",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the current Interface host state " "for an admitted namespace.",
                                "discriminant": "interface.get_interface_state.get_interface_state",
                                "name": "get_interface_state",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStatusRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStatusResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "get_interface_state",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Invoke a mounted API endpoint from " "Interface action context.",
                                "discriminant": "interface.invoke_interface_api.invoke_interface_api",
                                "name": "invoke_interface_api",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceInvokeApiRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceInvokeApiResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "invoke_interface_api",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Join an Environment session and "
                                "consume the Environment-owned default "
                                "navigation context.",
                                "discriminant": "interface.join_environment_session.join_environment_session",
                                "name": "join_environment_session",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "join_environment_session",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List locally admitted Interface "
                                "namespaces for operator/debug "
                                "surfaces.",
                                "discriminant": "interface.list_interface_namespaces.list_interface_namespaces",
                                "name": "list_interface_namespaces",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.NamespaceListRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.NamespaceListResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "list_interface_namespaces",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Commit one InterfaceSession-owned "
                                "portal to an existing "
                                "ExperienceSession authority.",
                                "discriminant": "interface.mount_interface_experience_session.mount_interface_experience_session",
                                "name": "mount_interface_experience_session",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "mount_interface_experience_session",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Dispatch a mounted Interface action "
                                "through the canonical service "
                                "boundary.",
                                "discriminant": "interface.perform_interface_action.perform_interface_action",
                                "name": "perform_interface_action",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceActionRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceActionResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "perform_interface_action",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read local Interface host readiness " "for service transport adapters.",
                                "discriminant": "interface.ping_interface_host.ping_interface_host",
                                "name": "ping_interface_host",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.PingRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.PingResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "ping_interface_host",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Report renderer capabilities for the " "admitted Interface namespace.",
                                "discriminant": "interface.report_renderer_capabilities.report_renderer_capabilities",
                                "name": "report_renderer_capabilities",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "report_renderer_capabilities",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Request a canonical Interface "
                                "window/layout/section binding for a "
                                "consumer action.",
                                "discriminant": "interface.request_interface_window_layout.request_interface_window_layout",
                                "name": "request_interface_window_layout",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "request_interface_window_layout",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve the current Interface focus "
                                "into an actor-specific Experience lens "
                                "over an admitted Environment session.",
                                "discriminant": "interface.resolve_experience_lens.resolve_experience_lens",
                                "name": "resolve_experience_lens",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "resolve_experience_lens",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Select the active Environment "
                                "Process/Thread target through "
                                "Interface-owned shell navigation.",
                                "discriminant": "interface.select_environment_navigation_target.select_environment_navigation_target",
                                "name": "select_environment_navigation_target",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "select_environment_navigation_target",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Select the active Interface control "
                                "profile for an admitted namespace.",
                                "discriminant": "interface.select_interface_profile.select_interface_profile",
                                "name": "select_interface_profile",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectProfileRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectProfileResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "select_interface_profile",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Select the active Interface runtime " "layout configuration.",
                                "discriminant": "interface.select_interface_runtime_layout.select_interface_runtime_layout",
                                "name": "select_interface_runtime_layout",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "select_interface_runtime_layout",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Select the active Interface "
                                "orchestration step for an admitted "
                                "namespace.",
                                "discriminant": "interface.select_interface_step.select_interface_step",
                                "name": "select_interface_step",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectStepRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectStepResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "select_interface_step",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Commit one Interface-owned shared door "
                                "rooted on a canonical Identity "
                                "Session.",
                                "discriminant": "interface.start_interface_session.start_interface_session",
                                "name": "start_interface_session",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionStartRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionStartResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "start_interface_session",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Stop one local Interface namespace.",
                                "discriminant": "interface.stop_interface_namespace.stop_interface_namespace",
                                "name": "stop_interface_namespace",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStopRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStopResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "stop_interface_namespace",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Invoke a mounted streaming API "
                                "endpoint from Interface action "
                                "context.",
                                "discriminant": "interface.stream_interface_api.stream_interface_api",
                                "name": "stream_interface_api",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStreamApiRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStreamApiResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed mounted " "API events.",
                                    "events": [
                                        {
                                            "class_ref": "aware_interface_service_dto.comms.models.InterfaceApiStreamClosedNotification",
                                            "kind": "complete",
                                            "source_path": "bindings/interface.apis.aware",
                                        },
                                        {
                                            "class_ref": "aware_interface_service_dto.comms.models.InterfaceApiEventNotification",
                                            "kind": "delta",
                                            "source_path": "bindings/interface.apis.aware",
                                        },
                                    ],
                                    "source_path": "bindings/interface.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "stream_interface_api",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Acknowledge consumed view-state "
                                "cursors for Interface renderer "
                                "backpressure.",
                                "discriminant": "interface.sync_view_state_cursor.sync_view_state_cursor",
                                "name": "sync_view_state_cursor",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "sync_view_state_cursor",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read and stream Interface host state "
                                "snapshots for an admitted namespace.",
                                "discriminant": "interface.watch_interface_state.watch_interface_state",
                                "name": "watch_interface_state",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceFollowRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceFollowResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed " "Interface host state " "snapshots.",
                                    "events": [
                                        {
                                            "class_ref": "aware_interface_service_dto.comms.models.InterfaceStateNotification",
                                            "kind": "snapshot",
                                            "source_path": "bindings/interface.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/interface.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_interface_state",
                        "source_path": "bindings/interface.apis.aware",
                    },
                ],
                "name": "interface",
                "source_path": "bindings/interface.apis.aware",
            }
        ],
        "fqn_prefix": "aware_interface_service_api",
        "package_name": "interface-service-api",
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
                                "description": "Activate an Interface runtime section "
                                "representation or focus target.",
                                "discriminant": "interface.activate_interface_runtime_focus.activate_interface_runtime_focus",
                                "endpoint_ref": "interface.activate_interface_runtime_focus.activate_interface_runtime_focus",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "activate_interface_runtime_focus",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceActivateRuntimeFocusRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceActivateRuntimeFocusResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "activate_interface_runtime_focus",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Admit the current Interface actor to "
                                "an Environment/Profile before "
                                "Experience lens resolution.",
                                "discriminant": "interface.admit_environment_actor.admit_environment_actor",
                                "endpoint_ref": "interface.admit_environment_actor.admit_environment_actor",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "admit_environment_actor",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceAdmitEnvironmentActorRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceAdmitEnvironmentActorResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "admit_environment_actor",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Admit or resume one renderer/agent "
                                "namespace into the Interface service "
                                "runtime.",
                                "discriminant": "interface.admit_interface.admit_interface",
                                "endpoint_ref": "interface.admit_interface.admit_interface",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "admit_interface",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.NamespaceEnsureRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.NamespaceEnsureRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.NamespaceEnsureResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.NamespaceEnsureResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "admit_interface",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Commit one complete "
                                "active-membership/order vector through "
                                "Interface Host and Attention "
                                "authority.",
                                "discriminant": "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition",
                                "endpoint_ref": "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "apply_attention_layout_topology_transition",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceApplyAttentionLayoutTopologyTransitionRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceApplyAttentionLayoutTopologyTransitionResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "apply_attention_layout_topology_transition",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Commit one complete shared-layout "
                                "vector through Interface Host and "
                                "Attention authority.",
                                "discriminant": "interface.apply_attention_layout_transition.apply_attention_layout_transition",
                                "endpoint_ref": "interface.apply_attention_layout_transition.apply_attention_layout_transition",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "apply_attention_layout_transition",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceApplyAttentionLayoutTransitionRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceApplyAttentionLayoutTransitionResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "apply_attention_layout_transition",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read one committed InterfaceSession "
                                "and its Interface-owned "
                                "ExperienceSession portal rows.",
                                "discriminant": "interface.describe_interface_session.describe_interface_session",
                                "endpoint_ref": "interface.describe_interface_session.describe_interface_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_interface_session",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionDescribeRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSessionDescribeRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionDescribeResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSessionDescribeResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "describe_interface_session",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Enter one committed AppPackage screen "
                                "through Interface Host and Experience "
                                "layout activation.",
                                "discriminant": "interface.enter_app_screen.enter_app_screen",
                                "endpoint_ref": "interface.enter_app_screen.enter_app_screen",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "enter_app_screen",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterAppScreenRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceEnterAppScreenRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterAppScreenResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceEnterAppScreenResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "enter_app_screen",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Enter or resume an Environment shell "
                                "context without Interface-owned "
                                "Process/Thread defaults.",
                                "discriminant": "interface.enter_environment.enter_environment",
                                "endpoint_ref": "interface.enter_environment.enter_environment",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "enter_environment",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceEnterEnvironmentRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceEnterEnvironmentResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "enter_environment",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the current Interface host state " "for an admitted namespace.",
                                "discriminant": "interface.get_interface_state.get_interface_state",
                                "endpoint_ref": "interface.get_interface_state.get_interface_state",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_interface_state",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStatusRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceStatusRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStatusResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceStatusResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "get_interface_state",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Invoke a mounted API endpoint from " "Interface action context.",
                                "discriminant": "interface.invoke_interface_api.invoke_interface_api",
                                "endpoint_ref": "interface.invoke_interface_api.invoke_interface_api",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "invoke_interface_api",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceInvokeApiRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceInvokeApiRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceInvokeApiResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceInvokeApiResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "invoke_interface_api",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Join an Environment session and "
                                "consume the Environment-owned default "
                                "navigation context.",
                                "discriminant": "interface.join_environment_session.join_environment_session",
                                "endpoint_ref": "interface.join_environment_session.join_environment_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "join_environment_session",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceJoinEnvironmentSessionRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceJoinEnvironmentSessionResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "join_environment_session",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List locally admitted Interface "
                                "namespaces for operator/debug "
                                "surfaces.",
                                "discriminant": "interface.list_interface_namespaces.list_interface_namespaces",
                                "endpoint_ref": "interface.list_interface_namespaces.list_interface_namespaces",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list_interface_namespaces",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.NamespaceListRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.NamespaceListRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.NamespaceListResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.NamespaceListResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "list_interface_namespaces",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Commit one InterfaceSession-owned "
                                "portal to an existing "
                                "ExperienceSession authority.",
                                "discriminant": "interface.mount_interface_experience_session.mount_interface_experience_session",
                                "endpoint_ref": "interface.mount_interface_experience_session.mount_interface_experience_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "mount_interface_experience_session",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceExperienceSessionMountRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceExperienceSessionMountResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "mount_interface_experience_session",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Dispatch a mounted Interface action "
                                "through the canonical service "
                                "boundary.",
                                "discriminant": "interface.perform_interface_action.perform_interface_action",
                                "endpoint_ref": "interface.perform_interface_action.perform_interface_action",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "perform_interface_action",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceActionRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceActionRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceActionResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceActionResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "perform_interface_action",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read local Interface host readiness " "for service transport adapters.",
                                "discriminant": "interface.ping_interface_host.ping_interface_host",
                                "endpoint_ref": "interface.ping_interface_host.ping_interface_host",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ping_interface_host",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.PingRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.PingRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.PingResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.PingResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "ping_interface_host",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Report renderer capabilities for the " "admitted Interface namespace.",
                                "discriminant": "interface.report_renderer_capabilities.report_renderer_capabilities",
                                "endpoint_ref": "interface.report_renderer_capabilities.report_renderer_capabilities",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "report_renderer_capabilities",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceReportRendererCapabilitiesRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceReportRendererCapabilitiesResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "report_renderer_capabilities",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Request a canonical Interface "
                                "window/layout/section binding for a "
                                "consumer action.",
                                "discriminant": "interface.request_interface_window_layout.request_interface_window_layout",
                                "endpoint_ref": "interface.request_interface_window_layout.request_interface_window_layout",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "request_interface_window_layout",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceRequestWindowLayoutRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceRequestWindowLayoutResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "request_interface_window_layout",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve the current Interface focus "
                                "into an actor-specific Experience lens "
                                "over an admitted Environment session.",
                                "discriminant": "interface.resolve_experience_lens.resolve_experience_lens",
                                "endpoint_ref": "interface.resolve_experience_lens.resolve_experience_lens",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_experience_lens",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceResolveExperienceLensRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceResolveExperienceLensResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "resolve_experience_lens",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Select the active Environment "
                                "Process/Thread target through "
                                "Interface-owned shell navigation.",
                                "discriminant": "interface.select_environment_navigation_target.select_environment_navigation_target",
                                "endpoint_ref": "interface.select_environment_navigation_target.select_environment_navigation_target",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "select_environment_navigation_target",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectEnvironmentNavigationTargetRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectEnvironmentNavigationTargetResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "select_environment_navigation_target",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Select the active Interface control "
                                "profile for an admitted namespace.",
                                "discriminant": "interface.select_interface_profile.select_interface_profile",
                                "endpoint_ref": "interface.select_interface_profile.select_interface_profile",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "select_interface_profile",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectProfileRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectProfileRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectProfileResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectProfileResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "select_interface_profile",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Select the active Interface runtime " "layout configuration.",
                                "discriminant": "interface.select_interface_runtime_layout.select_interface_runtime_layout",
                                "endpoint_ref": "interface.select_interface_runtime_layout.select_interface_runtime_layout",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "select_interface_runtime_layout",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectRuntimeLayoutRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectRuntimeLayoutResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "select_interface_runtime_layout",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Select the active Interface "
                                "orchestration step for an admitted "
                                "namespace.",
                                "discriminant": "interface.select_interface_step.select_interface_step",
                                "endpoint_ref": "interface.select_interface_step.select_interface_step",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "select_interface_step",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectStepRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectStepRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectStepResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectStepResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "select_interface_step",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Commit one Interface-owned shared door "
                                "rooted on a canonical Identity "
                                "Session.",
                                "discriminant": "interface.start_interface_session.start_interface_session",
                                "endpoint_ref": "interface.start_interface_session.start_interface_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "start_interface_session",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionStartRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSessionStartRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionStartResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSessionStartResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "start_interface_session",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Stop one local Interface namespace.",
                                "discriminant": "interface.stop_interface_namespace.stop_interface_namespace",
                                "endpoint_ref": "interface.stop_interface_namespace.stop_interface_namespace",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "stop_interface_namespace",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStopRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceStopRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStopResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceStopResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "stop_interface_namespace",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Invoke a mounted streaming API "
                                "endpoint from Interface action "
                                "context.",
                                "discriminant": "interface.stream_interface_api.stream_interface_api",
                                "endpoint_ref": "interface.stream_interface_api.stream_interface_api",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "stream_interface_api",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStreamApiRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceStreamApiRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStreamApiResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceStreamApiResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed mounted " "API events.",
                                    "events": [
                                        {
                                            "class_ref": "aware_interface_service_dto.comms.models.InterfaceApiStreamClosedNotification",
                                            "kind": "complete",
                                            "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceApiStreamClosedNotification",
                                            "source_path": "bindings/interface.apis.aware",
                                        },
                                        {
                                            "class_ref": "aware_interface_service_dto.comms.models.InterfaceApiEventNotification",
                                            "kind": "delta",
                                            "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceApiEventNotification",
                                            "source_path": "bindings/interface.apis.aware",
                                        },
                                    ],
                                    "source_path": "bindings/interface.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "stream_interface_api",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Acknowledge consumed view-state "
                                "cursors for Interface renderer "
                                "backpressure.",
                                "discriminant": "interface.sync_view_state_cursor.sync_view_state_cursor",
                                "endpoint_ref": "interface.sync_view_state_cursor.sync_view_state_cursor",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "sync_view_state_cursor",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSyncViewStateCursorRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceSyncViewStateCursorResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                            }
                        ],
                        "name": "sync_view_state_cursor",
                        "source_path": "bindings/interface.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read and stream Interface host state "
                                "snapshots for an admitted namespace.",
                                "discriminant": "interface.watch_interface_state.watch_interface_state",
                                "endpoint_ref": "interface.watch_interface_state.watch_interface_state",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "watch_interface_state",
                                "request": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceFollowRequest",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceFollowRequest",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceFollowResponse",
                                    "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceFollowResponse",
                                    "source_path": "bindings/interface.apis.aware",
                                },
                                "source_path": "bindings/interface.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed " "Interface host state " "snapshots.",
                                    "events": [
                                        {
                                            "class_ref": "aware_interface_service_dto.comms.models.InterfaceStateNotification",
                                            "kind": "snapshot",
                                            "python_model_ref": "aware_interface_service_dto.comms.models.control_plane.InterfaceStateNotification",
                                            "source_path": "bindings/interface.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/interface.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_interface_state",
                        "source_path": "bindings/interface.apis.aware",
                    },
                ],
                "name": "interface",
                "source_path": "bindings/interface.apis.aware",
            }
        ],
        "fqn_prefix": "aware_interface_service_api",
        "package_name": "interface-service-api",
        "schema_version": 1,
    }
)

INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_ENDPOINT_REF: Final[str] = (
    "interface.activate_interface_runtime_focus.activate_interface_runtime_focus"
)
INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_ENDPOINT_REF: Final[str] = (
    "interface.admit_environment_actor.admit_environment_actor"
)
INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_ENDPOINT_REF: Final[str] = "interface.admit_interface.admit_interface"
INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF: Final[
    str
] = "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition"
INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_ENDPOINT_REF: Final[str] = (
    "interface.apply_attention_layout_transition.apply_attention_layout_transition"
)
INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_ENDPOINT_REF: Final[str] = (
    "interface.describe_interface_session.describe_interface_session"
)
INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_ENDPOINT_REF: Final[str] = "interface.enter_app_screen.enter_app_screen"
INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_ENDPOINT_REF: Final[str] = (
    "interface.enter_environment.enter_environment"
)
INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_ENDPOINT_REF: Final[str] = (
    "interface.get_interface_state.get_interface_state"
)
INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_ENDPOINT_REF: Final[str] = (
    "interface.invoke_interface_api.invoke_interface_api"
)
INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_ENDPOINT_REF: Final[str] = (
    "interface.join_environment_session.join_environment_session"
)
INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_ENDPOINT_REF: Final[str] = (
    "interface.list_interface_namespaces.list_interface_namespaces"
)
INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_ENDPOINT_REF: Final[str] = (
    "interface.mount_interface_experience_session.mount_interface_experience_session"
)
INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_ENDPOINT_REF: Final[str] = (
    "interface.perform_interface_action.perform_interface_action"
)
INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_ENDPOINT_REF: Final[str] = (
    "interface.ping_interface_host.ping_interface_host"
)
INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_ENDPOINT_REF: Final[str] = (
    "interface.report_renderer_capabilities.report_renderer_capabilities"
)
INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_ENDPOINT_REF: Final[str] = (
    "interface.request_interface_window_layout.request_interface_window_layout"
)
INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_ENDPOINT_REF: Final[str] = (
    "interface.resolve_experience_lens.resolve_experience_lens"
)
INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_ENDPOINT_REF: Final[str] = (
    "interface.select_environment_navigation_target.select_environment_navigation_target"
)
INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_ENDPOINT_REF: Final[str] = (
    "interface.select_interface_profile.select_interface_profile"
)
INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_ENDPOINT_REF: Final[str] = (
    "interface.select_interface_runtime_layout.select_interface_runtime_layout"
)
INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_ENDPOINT_REF: Final[str] = (
    "interface.select_interface_step.select_interface_step"
)
INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_ENDPOINT_REF: Final[str] = (
    "interface.start_interface_session.start_interface_session"
)
INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_ENDPOINT_REF: Final[str] = (
    "interface.stop_interface_namespace.stop_interface_namespace"
)
INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF: Final[str] = (
    "interface.stream_interface_api.stream_interface_api"
)
INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_ENDPOINT_REF: Final[str] = (
    "interface.sync_view_state_cursor.sync_view_state_cursor"
)
INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF: Final[str] = (
    "interface.watch_interface_state.watch_interface_state"
)

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "interface.activate_interface_runtime_focus.activate_interface_runtime_focus": INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_ENDPOINT_REF,
    "interface.admit_environment_actor.admit_environment_actor": INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_ENDPOINT_REF,
    "interface.admit_interface.admit_interface": INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_ENDPOINT_REF,
    "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition": INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF,
    "interface.apply_attention_layout_transition.apply_attention_layout_transition": INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_ENDPOINT_REF,
    "interface.describe_interface_session.describe_interface_session": INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_ENDPOINT_REF,
    "interface.enter_app_screen.enter_app_screen": INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_ENDPOINT_REF,
    "interface.enter_environment.enter_environment": INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_ENDPOINT_REF,
    "interface.get_interface_state.get_interface_state": INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_ENDPOINT_REF,
    "interface.invoke_interface_api.invoke_interface_api": INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_ENDPOINT_REF,
    "interface.join_environment_session.join_environment_session": INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_ENDPOINT_REF,
    "interface.list_interface_namespaces.list_interface_namespaces": INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_ENDPOINT_REF,
    "interface.mount_interface_experience_session.mount_interface_experience_session": INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_ENDPOINT_REF,
    "interface.perform_interface_action.perform_interface_action": INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_ENDPOINT_REF,
    "interface.ping_interface_host.ping_interface_host": INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_ENDPOINT_REF,
    "interface.report_renderer_capabilities.report_renderer_capabilities": INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_ENDPOINT_REF,
    "interface.request_interface_window_layout.request_interface_window_layout": INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_ENDPOINT_REF,
    "interface.resolve_experience_lens.resolve_experience_lens": INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_ENDPOINT_REF,
    "interface.select_environment_navigation_target.select_environment_navigation_target": INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_ENDPOINT_REF,
    "interface.select_interface_profile.select_interface_profile": INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_ENDPOINT_REF,
    "interface.select_interface_runtime_layout.select_interface_runtime_layout": INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_ENDPOINT_REF,
    "interface.select_interface_step.select_interface_step": INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_ENDPOINT_REF,
    "interface.start_interface_session.start_interface_session": INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_ENDPOINT_REF,
    "interface.stop_interface_namespace.stop_interface_namespace": INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_ENDPOINT_REF,
    "interface.stream_interface_api.stream_interface_api": INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF,
    "interface.sync_view_state_cursor.sync_view_state_cursor": INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_ENDPOINT_REF,
    "interface.watch_interface_state.watch_interface_state": INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_ENDPOINT_REF",
    "INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_ENDPOINT_REF",
    "INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_ENDPOINT_REF",
    "INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF",
    "INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_ENDPOINT_REF",
    "INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_ENDPOINT_REF",
    "INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_ENDPOINT_REF",
    "INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_ENDPOINT_REF",
    "INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_ENDPOINT_REF",
    "INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_ENDPOINT_REF",
    "INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_ENDPOINT_REF",
    "INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_ENDPOINT_REF",
    "INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_ENDPOINT_REF",
    "INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_ENDPOINT_REF",
    "INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_ENDPOINT_REF",
    "INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_ENDPOINT_REF",
    "INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_ENDPOINT_REF",
    "INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_ENDPOINT_REF",
    "INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_ENDPOINT_REF",
    "INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_ENDPOINT_REF",
    "INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_ENDPOINT_REF",
    "INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_ENDPOINT_REF",
    "INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_ENDPOINT_REF",
    "INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_ENDPOINT_REF",
    "INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF",
    "INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_ENDPOINT_REF",
    "INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF",
]
