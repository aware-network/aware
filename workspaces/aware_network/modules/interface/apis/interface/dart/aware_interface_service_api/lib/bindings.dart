// GENERATED CODE - DO NOT MODIFY BY HAND
// Compiled API bindings for generated Dart SDK wrappers.

import 'dart:convert' as convert;

const String apiPackageName = "interface-service-api";
const String apiFqnPrefix = "aware_interface_service_api";

final Map<String, Object?> apiInterfaceSpecPayload = _decodeJsonObject(r'''
{
  "apis": [
    {
      "capabilities": [
        {
          "endpoints": [
            {
              "description": "Activate an Interface runtime section representation or focus target.",
              "discriminant": "interface.activate_interface_runtime_focus.activate_interface_runtime_focus",
              "name": "activate_interface_runtime_focus",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "activate_interface_runtime_focus",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Admit the current Interface actor to an Environment/Profile before Experience lens resolution.",
              "discriminant": "interface.admit_environment_actor.admit_environment_actor",
              "name": "admit_environment_actor",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "admit_environment_actor",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Admit or resume one renderer/agent namespace into the Interface service runtime.",
              "discriminant": "interface.admit_interface.admit_interface",
              "name": "admit_interface",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.NamespaceEnsureRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.NamespaceEnsureResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "admit_interface",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Commit one complete active-membership/order vector through Interface Host and Attention authority.",
              "discriminant": "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition",
              "name": "apply_attention_layout_topology_transition",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "apply_attention_layout_topology_transition",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Commit one complete shared-layout vector through Interface Host and Attention authority.",
              "discriminant": "interface.apply_attention_layout_transition.apply_attention_layout_transition",
              "name": "apply_attention_layout_transition",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "apply_attention_layout_transition",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Read one committed InterfaceSession and its Interface-owned ExperienceSession portal rows.",
              "discriminant": "interface.describe_interface_session.describe_interface_session",
              "name": "describe_interface_session",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionDescribeRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionDescribeResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "describe_interface_session",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Enter one committed AppPackage screen through Interface Host and Experience layout activation.",
              "discriminant": "interface.enter_app_screen.enter_app_screen",
              "name": "enter_app_screen",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterAppScreenRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterAppScreenResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "enter_app_screen",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Enter or resume an Environment shell context without Interface-owned Process/Thread defaults.",
              "discriminant": "interface.enter_environment.enter_environment",
              "name": "enter_environment",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "enter_environment",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Read the current Interface host state for an admitted namespace.",
              "discriminant": "interface.get_interface_state.get_interface_state",
              "name": "get_interface_state",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStatusRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStatusResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "get_interface_state",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Invoke a mounted API endpoint from Interface action context.",
              "discriminant": "interface.invoke_interface_api.invoke_interface_api",
              "name": "invoke_interface_api",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceInvokeApiRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceInvokeApiResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "invoke_interface_api",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Join an Environment session and consume the Environment-owned default navigation context.",
              "discriminant": "interface.join_environment_session.join_environment_session",
              "name": "join_environment_session",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "join_environment_session",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "List locally admitted Interface namespaces for operator/debug surfaces.",
              "discriminant": "interface.list_interface_namespaces.list_interface_namespaces",
              "name": "list_interface_namespaces",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.NamespaceListRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.NamespaceListResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "list_interface_namespaces",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Commit one InterfaceSession-owned portal to an existing ExperienceSession authority.",
              "discriminant": "interface.mount_interface_experience_session.mount_interface_experience_session",
              "name": "mount_interface_experience_session",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "mount_interface_experience_session",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Dispatch a mounted Interface action through the canonical service boundary.",
              "discriminant": "interface.perform_interface_action.perform_interface_action",
              "name": "perform_interface_action",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceActionRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceActionResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "perform_interface_action",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Read local Interface host readiness for service transport adapters.",
              "discriminant": "interface.ping_interface_host.ping_interface_host",
              "name": "ping_interface_host",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.PingRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.PingResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "ping_interface_host",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Report renderer capabilities for the admitted Interface namespace.",
              "discriminant": "interface.report_renderer_capabilities.report_renderer_capabilities",
              "name": "report_renderer_capabilities",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "report_renderer_capabilities",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Request a canonical Interface window/layout/section binding for a consumer action.",
              "discriminant": "interface.request_interface_window_layout.request_interface_window_layout",
              "name": "request_interface_window_layout",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "request_interface_window_layout",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Resolve the current Interface focus into an actor-specific Experience lens over an admitted Environment session.",
              "discriminant": "interface.resolve_experience_lens.resolve_experience_lens",
              "name": "resolve_experience_lens",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "resolve_experience_lens",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Select the active Environment Process/Thread target through Interface-owned shell navigation.",
              "discriminant": "interface.select_environment_navigation_target.select_environment_navigation_target",
              "name": "select_environment_navigation_target",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "select_environment_navigation_target",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Select the active Interface control profile for an admitted namespace.",
              "discriminant": "interface.select_interface_profile.select_interface_profile",
              "name": "select_interface_profile",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectProfileRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectProfileResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "select_interface_profile",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Select the active Interface runtime layout configuration.",
              "discriminant": "interface.select_interface_runtime_layout.select_interface_runtime_layout",
              "name": "select_interface_runtime_layout",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "select_interface_runtime_layout",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Select the active Interface orchestration step for an admitted namespace.",
              "discriminant": "interface.select_interface_step.select_interface_step",
              "name": "select_interface_step",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectStepRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectStepResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "select_interface_step",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Commit one Interface-owned shared door rooted on a canonical Identity Session.",
              "discriminant": "interface.start_interface_session.start_interface_session",
              "name": "start_interface_session",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionStartRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionStartResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "start_interface_session",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Stop one local Interface namespace.",
              "discriminant": "interface.stop_interface_namespace.stop_interface_namespace",
              "name": "stop_interface_namespace",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStopRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStopResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "stop_interface_namespace",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Invoke a mounted streaming API endpoint from Interface action context.",
              "discriminant": "interface.stream_interface_api.stream_interface_api",
              "name": "stream_interface_api",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStreamApiRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStreamApiResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware",
              "stream": {
                "description": "Canonical streamed mounted API events.",
                "events": [
                  {
                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApiStreamClosedNotification",
                    "kind": "complete",
                    "source_path": "bindings/interface.apis.aware"
                  },
                  {
                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApiEventNotification",
                    "kind": "delta",
                    "source_path": "bindings/interface.apis.aware"
                  }
                ],
                "source_path": "bindings/interface.apis.aware",
                "stream_mode": "server"
              }
            }
          ],
          "name": "stream_interface_api",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Acknowledge consumed view-state cursors for Interface renderer backpressure.",
              "discriminant": "interface.sync_view_state_cursor.sync_view_state_cursor",
              "name": "sync_view_state_cursor",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "sync_view_state_cursor",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Read and stream Interface host state snapshots for an admitted namespace.",
              "discriminant": "interface.watch_interface_state.watch_interface_state",
              "name": "watch_interface_state",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceFollowRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceFollowResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware",
              "stream": {
                "description": "Canonical streamed Interface host state snapshots.",
                "events": [
                  {
                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStateNotification",
                    "kind": "snapshot",
                    "source_path": "bindings/interface.apis.aware"
                  }
                ],
                "source_path": "bindings/interface.apis.aware",
                "stream_mode": "server"
              }
            }
          ],
          "name": "watch_interface_state",
          "source_path": "bindings/interface.apis.aware"
        }
      ],
      "name": "interface",
      "source_path": "bindings/interface.apis.aware"
    }
  ],
  "fqn_prefix": "aware_interface_service_api",
  "package_name": "interface-service-api",
  "schema_version": 1
}
''');

final Map<String, Object?> apiInvocationManifestPayload = _decodeJsonObject(r'''
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
              "description": "Activate an Interface runtime section representation or focus target.",
              "discriminant": "interface.activate_interface_runtime_focus.activate_interface_runtime_focus",
              "endpoint_ref": "interface.activate_interface_runtime_focus.activate_interface_runtime_focus",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "activate_interface_runtime_focus",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "activate_interface_runtime_focus",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Admit the current Interface actor to an Environment/Profile before Experience lens resolution.",
              "discriminant": "interface.admit_environment_actor.admit_environment_actor",
              "endpoint_ref": "interface.admit_environment_actor.admit_environment_actor",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "admit_environment_actor",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "admit_environment_actor",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Admit or resume one renderer/agent namespace into the Interface service runtime.",
              "discriminant": "interface.admit_interface.admit_interface",
              "endpoint_ref": "interface.admit_interface.admit_interface",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "admit_interface",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.NamespaceEnsureRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.NamespaceEnsureResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "admit_interface",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Commit one complete active-membership/order vector through Interface Host and Attention authority.",
              "discriminant": "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition",
              "endpoint_ref": "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "apply_attention_layout_topology_transition",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "apply_attention_layout_topology_transition",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Commit one complete shared-layout vector through Interface Host and Attention authority.",
              "discriminant": "interface.apply_attention_layout_transition.apply_attention_layout_transition",
              "endpoint_ref": "interface.apply_attention_layout_transition.apply_attention_layout_transition",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "apply_attention_layout_transition",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "apply_attention_layout_transition",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Read one committed InterfaceSession and its Interface-owned ExperienceSession portal rows.",
              "discriminant": "interface.describe_interface_session.describe_interface_session",
              "endpoint_ref": "interface.describe_interface_session.describe_interface_session",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "describe_interface_session",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionDescribeRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionDescribeResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "describe_interface_session",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Enter one committed AppPackage screen through Interface Host and Experience layout activation.",
              "discriminant": "interface.enter_app_screen.enter_app_screen",
              "endpoint_ref": "interface.enter_app_screen.enter_app_screen",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "enter_app_screen",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterAppScreenRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterAppScreenResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "enter_app_screen",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Enter or resume an Environment shell context without Interface-owned Process/Thread defaults.",
              "discriminant": "interface.enter_environment.enter_environment",
              "endpoint_ref": "interface.enter_environment.enter_environment",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "enter_environment",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "enter_environment",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Read the current Interface host state for an admitted namespace.",
              "discriminant": "interface.get_interface_state.get_interface_state",
              "endpoint_ref": "interface.get_interface_state.get_interface_state",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "get_interface_state",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStatusRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStatusResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "get_interface_state",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Invoke a mounted API endpoint from Interface action context.",
              "discriminant": "interface.invoke_interface_api.invoke_interface_api",
              "endpoint_ref": "interface.invoke_interface_api.invoke_interface_api",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "invoke_interface_api",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceInvokeApiRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceInvokeApiResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "invoke_interface_api",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Join an Environment session and consume the Environment-owned default navigation context.",
              "discriminant": "interface.join_environment_session.join_environment_session",
              "endpoint_ref": "interface.join_environment_session.join_environment_session",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "join_environment_session",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "join_environment_session",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "List locally admitted Interface namespaces for operator/debug surfaces.",
              "discriminant": "interface.list_interface_namespaces.list_interface_namespaces",
              "endpoint_ref": "interface.list_interface_namespaces.list_interface_namespaces",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "list_interface_namespaces",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.NamespaceListRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.NamespaceListResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "list_interface_namespaces",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Commit one InterfaceSession-owned portal to an existing ExperienceSession authority.",
              "discriminant": "interface.mount_interface_experience_session.mount_interface_experience_session",
              "endpoint_ref": "interface.mount_interface_experience_session.mount_interface_experience_session",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "mount_interface_experience_session",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "mount_interface_experience_session",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Dispatch a mounted Interface action through the canonical service boundary.",
              "discriminant": "interface.perform_interface_action.perform_interface_action",
              "endpoint_ref": "interface.perform_interface_action.perform_interface_action",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "perform_interface_action",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceActionRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceActionResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "perform_interface_action",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Read local Interface host readiness for service transport adapters.",
              "discriminant": "interface.ping_interface_host.ping_interface_host",
              "endpoint_ref": "interface.ping_interface_host.ping_interface_host",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "ping_interface_host",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.PingRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.PingResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "ping_interface_host",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Report renderer capabilities for the admitted Interface namespace.",
              "discriminant": "interface.report_renderer_capabilities.report_renderer_capabilities",
              "endpoint_ref": "interface.report_renderer_capabilities.report_renderer_capabilities",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "report_renderer_capabilities",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "report_renderer_capabilities",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Request a canonical Interface window/layout/section binding for a consumer action.",
              "discriminant": "interface.request_interface_window_layout.request_interface_window_layout",
              "endpoint_ref": "interface.request_interface_window_layout.request_interface_window_layout",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "request_interface_window_layout",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "request_interface_window_layout",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Resolve the current Interface focus into an actor-specific Experience lens over an admitted Environment session.",
              "discriminant": "interface.resolve_experience_lens.resolve_experience_lens",
              "endpoint_ref": "interface.resolve_experience_lens.resolve_experience_lens",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "resolve_experience_lens",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "resolve_experience_lens",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Select the active Environment Process/Thread target through Interface-owned shell navigation.",
              "discriminant": "interface.select_environment_navigation_target.select_environment_navigation_target",
              "endpoint_ref": "interface.select_environment_navigation_target.select_environment_navigation_target",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "select_environment_navigation_target",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "select_environment_navigation_target",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Select the active Interface control profile for an admitted namespace.",
              "discriminant": "interface.select_interface_profile.select_interface_profile",
              "endpoint_ref": "interface.select_interface_profile.select_interface_profile",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "select_interface_profile",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectProfileRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectProfileResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "select_interface_profile",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Select the active Interface runtime layout configuration.",
              "discriminant": "interface.select_interface_runtime_layout.select_interface_runtime_layout",
              "endpoint_ref": "interface.select_interface_runtime_layout.select_interface_runtime_layout",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "select_interface_runtime_layout",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "select_interface_runtime_layout",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Select the active Interface orchestration step for an admitted namespace.",
              "discriminant": "interface.select_interface_step.select_interface_step",
              "endpoint_ref": "interface.select_interface_step.select_interface_step",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "select_interface_step",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectStepRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSelectStepResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "select_interface_step",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Commit one Interface-owned shared door rooted on a canonical Identity Session.",
              "discriminant": "interface.start_interface_session.start_interface_session",
              "endpoint_ref": "interface.start_interface_session.start_interface_session",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "start_interface_session",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionStartRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSessionStartResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "start_interface_session",
          "source_path": "bindings/interface.apis.aware"
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
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStopResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "stop_interface_namespace",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Invoke a mounted streaming API endpoint from Interface action context.",
              "discriminant": "interface.stream_interface_api.stream_interface_api",
              "endpoint_ref": "interface.stream_interface_api.stream_interface_api",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "stream_interface_api",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStreamApiRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceStreamApiResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware",
              "stream": {
                "description": "Canonical streamed mounted API events.",
                "events": [
                  {
                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApiStreamClosedNotification",
                    "kind": "complete",
                    "source_path": "bindings/interface.apis.aware"
                  },
                  {
                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceApiEventNotification",
                    "kind": "delta",
                    "source_path": "bindings/interface.apis.aware"
                  }
                ],
                "source_path": "bindings/interface.apis.aware",
                "stream_mode": "server"
              }
            }
          ],
          "name": "stream_interface_api",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Acknowledge consumed view-state cursors for Interface renderer backpressure.",
              "discriminant": "interface.sync_view_state_cursor.sync_view_state_cursor",
              "endpoint_ref": "interface.sync_view_state_cursor.sync_view_state_cursor",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "sync_view_state_cursor",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware"
            }
          ],
          "name": "sync_view_state_cursor",
          "source_path": "bindings/interface.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Read and stream Interface host state snapshots for an admitted namespace.",
              "discriminant": "interface.watch_interface_state.watch_interface_state",
              "endpoint_ref": "interface.watch_interface_state.watch_interface_state",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "watch_interface_state",
              "request": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceFollowRequest",
                "source_path": "bindings/interface.apis.aware"
              },
              "response": {
                "class_ref": "aware_interface_service_dto.comms.models.InterfaceFollowResponse",
                "source_path": "bindings/interface.apis.aware"
              },
              "source_path": "bindings/interface.apis.aware",
              "stream": {
                "description": "Canonical streamed Interface host state snapshots.",
                "events": [
                  {
                    "class_ref": "aware_interface_service_dto.comms.models.InterfaceStateNotification",
                    "kind": "snapshot",
                    "source_path": "bindings/interface.apis.aware"
                  }
                ],
                "source_path": "bindings/interface.apis.aware",
                "stream_mode": "server"
              }
            }
          ],
          "name": "watch_interface_state",
          "source_path": "bindings/interface.apis.aware"
        }
      ],
      "name": "interface",
      "source_path": "bindings/interface.apis.aware"
    }
  ],
  "fqn_prefix": "aware_interface_service_api",
  "package_name": "interface-service-api",
  "schema_version": 1
}
''');

const String
interfaceActivateInterfaceRuntimeFocusActivateInterfaceRuntimeFocusEndpointRef =
    "interface.activate_interface_runtime_focus.activate_interface_runtime_focus";
const String
interfaceActivateInterfaceRuntimeFocusActivateInterfaceRuntimeFocusDiscriminant =
    "interface.activate_interface_runtime_focus.activate_interface_runtime_focus";
const String interfaceAdmitEnvironmentActorAdmitEnvironmentActorEndpointRef =
    "interface.admit_environment_actor.admit_environment_actor";
const String interfaceAdmitEnvironmentActorAdmitEnvironmentActorDiscriminant =
    "interface.admit_environment_actor.admit_environment_actor";
const String interfaceAdmitInterfaceAdmitInterfaceEndpointRef =
    "interface.admit_interface.admit_interface";
const String interfaceAdmitInterfaceAdmitInterfaceDiscriminant =
    "interface.admit_interface.admit_interface";
const String
interfaceApplyAttentionLayoutTopologyTransitionApplyAttentionLayoutTopologyTransitionEndpointRef =
    "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition";
const String
interfaceApplyAttentionLayoutTopologyTransitionApplyAttentionLayoutTopologyTransitionDiscriminant =
    "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition";
const String
interfaceApplyAttentionLayoutTransitionApplyAttentionLayoutTransitionEndpointRef =
    "interface.apply_attention_layout_transition.apply_attention_layout_transition";
const String
interfaceApplyAttentionLayoutTransitionApplyAttentionLayoutTransitionDiscriminant =
    "interface.apply_attention_layout_transition.apply_attention_layout_transition";
const String
interfaceDescribeInterfaceSessionDescribeInterfaceSessionEndpointRef =
    "interface.describe_interface_session.describe_interface_session";
const String
interfaceDescribeInterfaceSessionDescribeInterfaceSessionDiscriminant =
    "interface.describe_interface_session.describe_interface_session";
const String interfaceEnterAppScreenEnterAppScreenEndpointRef =
    "interface.enter_app_screen.enter_app_screen";
const String interfaceEnterAppScreenEnterAppScreenDiscriminant =
    "interface.enter_app_screen.enter_app_screen";
const String interfaceEnterEnvironmentEnterEnvironmentEndpointRef =
    "interface.enter_environment.enter_environment";
const String interfaceEnterEnvironmentEnterEnvironmentDiscriminant =
    "interface.enter_environment.enter_environment";
const String interfaceGetInterfaceStateGetInterfaceStateEndpointRef =
    "interface.get_interface_state.get_interface_state";
const String interfaceGetInterfaceStateGetInterfaceStateDiscriminant =
    "interface.get_interface_state.get_interface_state";
const String interfaceInvokeInterfaceApiInvokeInterfaceApiEndpointRef =
    "interface.invoke_interface_api.invoke_interface_api";
const String interfaceInvokeInterfaceApiInvokeInterfaceApiDiscriminant =
    "interface.invoke_interface_api.invoke_interface_api";
const String interfaceJoinEnvironmentSessionJoinEnvironmentSessionEndpointRef =
    "interface.join_environment_session.join_environment_session";
const String interfaceJoinEnvironmentSessionJoinEnvironmentSessionDiscriminant =
    "interface.join_environment_session.join_environment_session";
const String
interfaceListInterfaceNamespacesListInterfaceNamespacesEndpointRef =
    "interface.list_interface_namespaces.list_interface_namespaces";
const String
interfaceListInterfaceNamespacesListInterfaceNamespacesDiscriminant =
    "interface.list_interface_namespaces.list_interface_namespaces";
const String
interfaceMountInterfaceExperienceSessionMountInterfaceExperienceSessionEndpointRef =
    "interface.mount_interface_experience_session.mount_interface_experience_session";
const String
interfaceMountInterfaceExperienceSessionMountInterfaceExperienceSessionDiscriminant =
    "interface.mount_interface_experience_session.mount_interface_experience_session";
const String interfacePerformInterfaceActionPerformInterfaceActionEndpointRef =
    "interface.perform_interface_action.perform_interface_action";
const String interfacePerformInterfaceActionPerformInterfaceActionDiscriminant =
    "interface.perform_interface_action.perform_interface_action";
const String interfacePingInterfaceHostPingInterfaceHostEndpointRef =
    "interface.ping_interface_host.ping_interface_host";
const String interfacePingInterfaceHostPingInterfaceHostDiscriminant =
    "interface.ping_interface_host.ping_interface_host";
const String
interfaceReportRendererCapabilitiesReportRendererCapabilitiesEndpointRef =
    "interface.report_renderer_capabilities.report_renderer_capabilities";
const String
interfaceReportRendererCapabilitiesReportRendererCapabilitiesDiscriminant =
    "interface.report_renderer_capabilities.report_renderer_capabilities";
const String
interfaceRequestInterfaceWindowLayoutRequestInterfaceWindowLayoutEndpointRef =
    "interface.request_interface_window_layout.request_interface_window_layout";
const String
interfaceRequestInterfaceWindowLayoutRequestInterfaceWindowLayoutDiscriminant =
    "interface.request_interface_window_layout.request_interface_window_layout";
const String interfaceResolveExperienceLensResolveExperienceLensEndpointRef =
    "interface.resolve_experience_lens.resolve_experience_lens";
const String interfaceResolveExperienceLensResolveExperienceLensDiscriminant =
    "interface.resolve_experience_lens.resolve_experience_lens";
const String
interfaceSelectEnvironmentNavigationTargetSelectEnvironmentNavigationTargetEndpointRef =
    "interface.select_environment_navigation_target.select_environment_navigation_target";
const String
interfaceSelectEnvironmentNavigationTargetSelectEnvironmentNavigationTargetDiscriminant =
    "interface.select_environment_navigation_target.select_environment_navigation_target";
const String interfaceSelectInterfaceProfileSelectInterfaceProfileEndpointRef =
    "interface.select_interface_profile.select_interface_profile";
const String interfaceSelectInterfaceProfileSelectInterfaceProfileDiscriminant =
    "interface.select_interface_profile.select_interface_profile";
const String
interfaceSelectInterfaceRuntimeLayoutSelectInterfaceRuntimeLayoutEndpointRef =
    "interface.select_interface_runtime_layout.select_interface_runtime_layout";
const String
interfaceSelectInterfaceRuntimeLayoutSelectInterfaceRuntimeLayoutDiscriminant =
    "interface.select_interface_runtime_layout.select_interface_runtime_layout";
const String interfaceSelectInterfaceStepSelectInterfaceStepEndpointRef =
    "interface.select_interface_step.select_interface_step";
const String interfaceSelectInterfaceStepSelectInterfaceStepDiscriminant =
    "interface.select_interface_step.select_interface_step";
const String interfaceStartInterfaceSessionStartInterfaceSessionEndpointRef =
    "interface.start_interface_session.start_interface_session";
const String interfaceStartInterfaceSessionStartInterfaceSessionDiscriminant =
    "interface.start_interface_session.start_interface_session";
const String interfaceStopInterfaceNamespaceStopInterfaceNamespaceEndpointRef =
    "interface.stop_interface_namespace.stop_interface_namespace";
const String interfaceStopInterfaceNamespaceStopInterfaceNamespaceDiscriminant =
    "interface.stop_interface_namespace.stop_interface_namespace";
const String interfaceStreamInterfaceApiStreamInterfaceApiEndpointRef =
    "interface.stream_interface_api.stream_interface_api";
const String interfaceStreamInterfaceApiStreamInterfaceApiDiscriminant =
    "interface.stream_interface_api.stream_interface_api";
const String interfaceSyncViewStateCursorSyncViewStateCursorEndpointRef =
    "interface.sync_view_state_cursor.sync_view_state_cursor";
const String interfaceSyncViewStateCursorSyncViewStateCursorDiscriminant =
    "interface.sync_view_state_cursor.sync_view_state_cursor";
const String interfaceWatchInterfaceStateWatchInterfaceStateEndpointRef =
    "interface.watch_interface_state.watch_interface_state";
const String interfaceWatchInterfaceStateWatchInterfaceStateDiscriminant =
    "interface.watch_interface_state.watch_interface_state";

Map<String, Object?> _decodeJsonObject(String raw) {
  final decoded = convert.jsonDecode(raw);
  if (decoded is! Map) {
    throw StateError(
      'Expected compiled API payload to decode to a JSON object.',
    );
  }
  return Map<String, Object?>.from(decoded);
}
