# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "experience-service-api"
API_FQN_PREFIX: Final[str] = "aware_experience_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Activate one Experience layout graph "
                                "binding through its grouped section "
                                "graph bindings.",
                                "discriminant": "experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding",
                                "name": "activate_experience_layout_graph_binding",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceLayoutGraphBindingRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceLayoutGraphBindingResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "activate_experience_layout_graph_binding",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Activate one Experience section graph "
                                "binding through the canonical "
                                "Experience coordination seam.",
                                "discriminant": "experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding",
                                "name": "activate_experience_section_graph_binding",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceSectionGraphBindingRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceSectionGraphBindingResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "activate_experience_section_graph_binding",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Admit one actor under an Experience "
                                "ActorConfig and return Identity-backed "
                                "role assignment evidence.",
                                "discriminant": "experience.actor_admission.admit_experience_actor_config",
                                "name": "admit_experience_actor_config",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.actor_admission.AdmitExperienceActorConfigRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.actor_admission.AdmitExperienceActorConfigResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "actor_admission",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Apply an Experience-owned View -> "
                                "Event -> View transition through a "
                                "target section-graph binding.",
                                "discriminant": "experience.apply_experience_view_event_transition.apply_experience_view_event_transition",
                                "name": "apply_experience_view_event_transition",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ApplyExperienceViewEventTransitionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ApplyExperienceViewEventTransitionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "apply_experience_view_event_transition",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Describe one committed "
                                "ExperienceSession through the "
                                "Experience-owned projection read "
                                "model.",
                                "discriminant": "experience.describe_experience_session.describe_experience_session",
                                "name": "describe_experience_session",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.DescribeExperienceSessionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.DescribeExperienceSessionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "describe_experience_session",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Execute Experience-owned "
                                "EnvironmentExperience profile program "
                                "apply declarations.",
                                "discriminant": "experience.environment_profile.apply_experience_environment_profile_programs",
                                "name": "apply_experience_environment_profile_programs",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.ApplyExperienceEnvironmentProfileProgramsRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.ApplyExperienceEnvironmentProfileProgramsResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "description": "Provision one Experience-owned "
                                "EnvironmentExperience profile topology "
                                "seed.",
                                "discriminant": "experience.environment_profile.provision_experience_environment_profile",
                                "name": "provision_experience_environment_profile",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.ProvisionExperienceEnvironmentProfileRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.ProvisionExperienceEnvironmentProfileResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "description": "Resolve and upsert one "
                                "Experience-owned EnvironmentExperience "
                                "profile contract.",
                                "discriminant": "experience.environment_profile.upsert_experience_environment_profile",
                                "name": "upsert_experience_environment_profile",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.UpsertExperienceEnvironmentProfileRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.UpsertExperienceEnvironmentProfileResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                        ],
                        "name": "environment_profile",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the canonical Experience "
                                "layout-graph-binding catalog for one "
                                "Experience.",
                                "discriminant": "experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog",
                                "name": "get_experience_layout_graph_binding_catalog",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingCatalogRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingCatalogResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "get_experience_layout_graph_binding_catalog",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read current Attention-backed state "
                                "for one Experience layout graph "
                                "binding.",
                                "discriminant": "experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state",
                                "name": "get_experience_layout_graph_binding_state",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingStateRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingStateResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "get_experience_layout_graph_binding_state",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the canonical "
                                "section-graph-binding catalog for one "
                                "Experience.",
                                "discriminant": "experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog",
                                "name": "get_experience_section_graph_binding_catalog",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingCatalogRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingCatalogResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "get_experience_section_graph_binding_catalog",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the current Attention-backed "
                                "state for one Experience section graph "
                                "binding.",
                                "discriminant": "experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state",
                                "name": "get_experience_section_graph_binding_state",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingStateRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingStateResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "get_experience_section_graph_binding_state",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Invoke one API-backed view action "
                                "through Experience and record its "
                                "Service/API receipt provenance.",
                                "discriminant": "experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action",
                                "name": "invoke_experience_view_invocation_action",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.InvokeExperienceViewInvocationActionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.InvokeExperienceViewInvocationActionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "invoke_experience_view_invocation_action",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Commit one session-local Experience "
                                "profile mount without selecting global "
                                "active state.",
                                "discriminant": "experience.mount_experience_session_profile.mount_experience_session_profile",
                                "name": "mount_experience_session_profile",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.MountExperienceSessionProfileRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.MountExperienceSessionProfileResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "mount_experience_session_profile",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve Experience package projection "
                                "ownership and consumer requirements "
                                "without exposing runtime internals.",
                                "discriminant": "experience.package_materialization.resolve_experience_package_projection_ownership",
                                "name": "resolve_experience_package_projection_ownership",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.package_materialization.ResolveExperiencePackageProjectionOwnershipRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.package_materialization.ResolveExperiencePackageProjectionOwnershipResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "package_materialization",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Apply one pre-resolved Experience " "program reference.",
                                "discriminant": "experience.program.apply_program_ref",
                                "name": "apply_program_ref",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.program.ApplyProgramRefRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.program.ApplyProgramRefResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "description": "Read one Experience-owned Program turn " "execution.",
                                "discriminant": "experience.program.get_turn_execution",
                                "name": "get_turn_execution",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.program.GetTurnExecutionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.program.GetTurnExecutionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "description": "Run one Experience-owned Program "
                                "through the Experience API boundary.",
                                "discriminant": "experience.program.run_program",
                                "name": "run_program",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.program.RunProgramRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.program.RunProgramResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "description": "Submit one Experience-owned Program " "turn.",
                                "discriminant": "experience.program.submit_program_turn",
                                "name": "submit_program_turn",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.program.SubmitProgramTurnRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.program.SubmitProgramTurnResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                        ],
                        "name": "program",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Record one concrete invocation action "
                                "through a resolved Experience view "
                                "instance.",
                                "discriminant": "experience.record_experience_view_invocation_action.record_experience_view_invocation_action",
                                "name": "record_experience_view_invocation_action",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.RecordExperienceViewInvocationActionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.RecordExperienceViewInvocationActionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "record_experience_view_invocation_action",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Request one Experience layout "
                                "transition through Experience -> "
                                "Attention.",
                                "discriminant": "experience.request_experience_layout_transition.request_experience_layout_transition",
                                "name": "request_experience_layout_transition",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.layout_transition.RequestExperienceLayoutTransitionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.layout_transition.RequestExperienceLayoutTransitionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "request_experience_layout_transition",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve declared Experience role "
                                "policy for one invocation action "
                                "config without authorizing a concrete "
                                "actor.",
                                "discriminant": "experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy",
                                "name": "resolve_experience_invocation_action_role_policy",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ResolveExperienceInvocationActionRolePolicyRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ResolveExperienceInvocationActionRolePolicyResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "resolve_experience_invocation_action_role_policy",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve a semantic Experience intent "
                                "into config-level Thread-Layout "
                                "targets and evidence.",
                                "discriminant": "experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent",
                                "name": "resolve_experience_thread_layout_intent",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.thread_layout_resolution.ResolveExperienceThreadLayoutIntentRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.thread_layout_resolution.ResolveExperienceThreadLayoutIntentResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "resolve_experience_thread_layout_intent",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve actor-specific Experience "
                                "session context over Environment "
                                "session Attention resolution.",
                                "discriminant": "experience.session_context.resolve_experience_session_context",
                                "name": "resolve_experience_session_context",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_context.ResolveExperienceSessionContextRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_context.ResolveExperienceSessionContextResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "session_context",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Admit an actor to an Experience "
                                "session and ensure one Experience "
                                "session feature.",
                                "discriminant": "experience.session_handoff.ensure_experience_session_handoff",
                                "name": "ensure_experience_session_handoff",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_handoff.EnsureExperienceSessionHandoffRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_handoff.EnsureExperienceSessionHandoffResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "description": "Read Experience session actor "
                                "admission and session feature lease "
                                "health.",
                                "discriminant": "experience.session_handoff.get_experience_session_handoff_status",
                                "name": "get_experience_session_handoff_status",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_handoff.GetExperienceSessionHandoffStatusRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_handoff.GetExperienceSessionHandoffStatusResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                        ],
                        "name": "session_handoff",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve a consumer read frame over "
                                "actor-specific Experience context and "
                                "shared Environment Attention.",
                                "discriminant": "experience.session_view_frame.resolve_experience_session_view_frame",
                                "name": "resolve_experience_session_view_frame",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_view_frame.ResolveExperienceSessionViewFrameRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_view_frame.ResolveExperienceSessionViewFrameResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "session_view_frame",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Commit one ExperienceSession rooted on "
                                "a child Identity Session with explicit "
                                "EnvironmentSession provenance.",
                                "discriminant": "experience.start_experience_session.start_experience_session",
                                "name": "start_experience_session",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.StartExperienceSessionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.StartExperienceSessionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "start_experience_session",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read and stream Experience " "section-graph-binding state snapshots.",
                                "discriminant": "experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings",
                                "name": "watch_experience_section_graph_bindings",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.WatchExperienceSectionGraphBindingsRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.WatchExperienceSectionGraphBindingsResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed "
                                    "Experience "
                                    "section-graph-binding "
                                    "snapshots.",
                                    "events": [
                                        {
                                            "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ExperienceSectionGraphBindingStateEvent",
                                            "kind": "snapshot",
                                            "source_path": "bindings/experience.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/experience.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_experience_section_graph_bindings",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read and stream Experience-owned "
                                "view-state snapshots for one mounted "
                                "view subscription.",
                                "discriminant": "experience.watch_experience_view_state.watch_experience_view_state",
                                "name": "watch_experience_view_state",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.view_state.WatchExperienceViewStateRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.view_state.WatchExperienceViewStateResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed " "Experience view-state " "snapshots.",
                                    "events": [
                                        {
                                            "class_ref": "aware_experience_service_dto.experience.view_state.ExperienceViewStateEvent",
                                            "kind": "snapshot",
                                            "source_path": "bindings/experience.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/experience.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_experience_view_state",
                        "source_path": "bindings/experience.apis.aware",
                    },
                ],
                "name": "experience",
                "source_path": "bindings/experience.apis.aware",
            }
        ],
        "fqn_prefix": "aware_experience_service_api",
        "package_name": "experience-service-api",
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
                                "description": "Activate one Experience layout graph "
                                "binding through its grouped section "
                                "graph bindings.",
                                "discriminant": "experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding",
                                "endpoint_ref": "experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "activate_experience_layout_graph_binding",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceLayoutGraphBindingRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ActivateExperienceLayoutGraphBindingRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceLayoutGraphBindingResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ActivateExperienceLayoutGraphBindingResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "activate_experience_layout_graph_binding",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Activate one Experience section graph "
                                "binding through the canonical "
                                "Experience coordination seam.",
                                "discriminant": "experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding",
                                "endpoint_ref": "experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "activate_experience_section_graph_binding",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceSectionGraphBindingRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ActivateExperienceSectionGraphBindingRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceSectionGraphBindingResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ActivateExperienceSectionGraphBindingResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "activate_experience_section_graph_binding",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Admit one actor under an Experience "
                                "ActorConfig and return Identity-backed "
                                "role assignment evidence.",
                                "discriminant": "experience.actor_admission.admit_experience_actor_config",
                                "endpoint_ref": "experience.actor_admission.admit_experience_actor_config",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "admit_experience_actor_config",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.actor_admission.AdmitExperienceActorConfigRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.actor_admission.service_operation.AdmitExperienceActorConfigRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.actor_admission.AdmitExperienceActorConfigResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.actor_admission.service_operation.AdmitExperienceActorConfigResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "actor_admission",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Apply an Experience-owned View -> "
                                "Event -> View transition through a "
                                "target section-graph binding.",
                                "discriminant": "experience.apply_experience_view_event_transition.apply_experience_view_event_transition",
                                "endpoint_ref": "experience.apply_experience_view_event_transition.apply_experience_view_event_transition",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "apply_experience_view_event_transition",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ApplyExperienceViewEventTransitionRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ApplyExperienceViewEventTransitionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ApplyExperienceViewEventTransitionResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ApplyExperienceViewEventTransitionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "apply_experience_view_event_transition",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe one committed "
                                "ExperienceSession through the "
                                "Experience-owned projection read "
                                "model.",
                                "discriminant": "experience.describe_experience_session.describe_experience_session",
                                "endpoint_ref": "experience.describe_experience_session.describe_experience_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_experience_session",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.DescribeExperienceSessionRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_commit.service_operation.DescribeExperienceSessionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.DescribeExperienceSessionResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_commit.service_operation.DescribeExperienceSessionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "describe_experience_session",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Execute Experience-owned "
                                "EnvironmentExperience profile program "
                                "apply declarations.",
                                "discriminant": "experience.environment_profile.apply_experience_environment_profile_programs",
                                "endpoint_ref": "experience.environment_profile.apply_experience_environment_profile_programs",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "apply_experience_environment_profile_programs",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.ApplyExperienceEnvironmentProfileProgramsRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.environment_profile.service_operation.ApplyExperienceEnvironmentProfileProgramsRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.ApplyExperienceEnvironmentProfileProgramsResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.environment_profile.service_operation.ApplyExperienceEnvironmentProfileProgramsResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Provision one Experience-owned "
                                "EnvironmentExperience profile topology "
                                "seed.",
                                "discriminant": "experience.environment_profile.provision_experience_environment_profile",
                                "endpoint_ref": "experience.environment_profile.provision_experience_environment_profile",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "provision_experience_environment_profile",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.ProvisionExperienceEnvironmentProfileRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.environment_profile.service_operation.ProvisionExperienceEnvironmentProfileRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.ProvisionExperienceEnvironmentProfileResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.environment_profile.service_operation.ProvisionExperienceEnvironmentProfileResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve and upsert one "
                                "Experience-owned EnvironmentExperience "
                                "profile contract.",
                                "discriminant": "experience.environment_profile.upsert_experience_environment_profile",
                                "endpoint_ref": "experience.environment_profile.upsert_experience_environment_profile",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "upsert_experience_environment_profile",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.UpsertExperienceEnvironmentProfileRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.environment_profile.service_operation.UpsertExperienceEnvironmentProfileRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.environment_profile.UpsertExperienceEnvironmentProfileResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.environment_profile.service_operation.UpsertExperienceEnvironmentProfileResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                        ],
                        "name": "environment_profile",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the canonical Experience "
                                "layout-graph-binding catalog for one "
                                "Experience.",
                                "discriminant": "experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog",
                                "endpoint_ref": "experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_experience_layout_graph_binding_catalog",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingCatalogRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceLayoutGraphBindingCatalogRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingCatalogResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceLayoutGraphBindingCatalogResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "get_experience_layout_graph_binding_catalog",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read current Attention-backed state "
                                "for one Experience layout graph "
                                "binding.",
                                "discriminant": "experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state",
                                "endpoint_ref": "experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_experience_layout_graph_binding_state",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingStateRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceLayoutGraphBindingStateRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingStateResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceLayoutGraphBindingStateResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "get_experience_layout_graph_binding_state",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the canonical "
                                "section-graph-binding catalog for one "
                                "Experience.",
                                "discriminant": "experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog",
                                "endpoint_ref": "experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_experience_section_graph_binding_catalog",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingCatalogRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceSectionGraphBindingCatalogRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingCatalogResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceSectionGraphBindingCatalogResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "get_experience_section_graph_binding_catalog",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the current Attention-backed "
                                "state for one Experience section graph "
                                "binding.",
                                "discriminant": "experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state",
                                "endpoint_ref": "experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_experience_section_graph_binding_state",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingStateRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceSectionGraphBindingStateRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingStateResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceSectionGraphBindingStateResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "get_experience_section_graph_binding_state",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Invoke one API-backed view action "
                                "through Experience and record its "
                                "Service/API receipt provenance.",
                                "discriminant": "experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action",
                                "endpoint_ref": "experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "invoke_experience_view_invocation_action",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.InvokeExperienceViewInvocationActionRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.InvokeExperienceViewInvocationActionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.InvokeExperienceViewInvocationActionResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.InvokeExperienceViewInvocationActionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "invoke_experience_view_invocation_action",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Commit one session-local Experience "
                                "profile mount without selecting global "
                                "active state.",
                                "discriminant": "experience.mount_experience_session_profile.mount_experience_session_profile",
                                "endpoint_ref": "experience.mount_experience_session_profile.mount_experience_session_profile",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "mount_experience_session_profile",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.MountExperienceSessionProfileRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_commit.service_operation.MountExperienceSessionProfileRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.MountExperienceSessionProfileResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_commit.service_operation.MountExperienceSessionProfileResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "mount_experience_session_profile",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve Experience package projection "
                                "ownership and consumer requirements "
                                "without exposing runtime internals.",
                                "discriminant": "experience.package_materialization.resolve_experience_package_projection_ownership",
                                "endpoint_ref": "experience.package_materialization.resolve_experience_package_projection_ownership",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_experience_package_projection_ownership",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.package_materialization.ResolveExperiencePackageProjectionOwnershipRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.package_materialization.service_operation.ResolveExperiencePackageProjectionOwnershipRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.package_materialization.ResolveExperiencePackageProjectionOwnershipResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.package_materialization.service_operation.ResolveExperiencePackageProjectionOwnershipResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "package_materialization",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Apply one pre-resolved Experience " "program reference.",
                                "discriminant": "experience.program.apply_program_ref",
                                "endpoint_ref": "experience.program.apply_program_ref",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "apply_program_ref",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.program.ApplyProgramRefRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.program.service_operation.ApplyProgramRefRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.program.ApplyProgramRefResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.program.service_operation.ApplyProgramRefResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read one Experience-owned Program turn " "execution.",
                                "discriminant": "experience.program.get_turn_execution",
                                "endpoint_ref": "experience.program.get_turn_execution",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_turn_execution",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.program.GetTurnExecutionRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.program.service_operation.GetTurnExecutionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.program.GetTurnExecutionResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.program.service_operation.GetTurnExecutionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Run one Experience-owned Program "
                                "through the Experience API boundary.",
                                "discriminant": "experience.program.run_program",
                                "endpoint_ref": "experience.program.run_program",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "run_program",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.program.RunProgramRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.program.service_operation.RunProgramRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.program.RunProgramResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.program.service_operation.RunProgramResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Submit one Experience-owned Program " "turn.",
                                "discriminant": "experience.program.submit_program_turn",
                                "endpoint_ref": "experience.program.submit_program_turn",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "submit_program_turn",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.program.SubmitProgramTurnRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.program.service_operation.SubmitProgramTurnRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.program.SubmitProgramTurnResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.program.service_operation.SubmitProgramTurnResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                        ],
                        "name": "program",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Record one concrete invocation action "
                                "through a resolved Experience view "
                                "instance.",
                                "discriminant": "experience.record_experience_view_invocation_action.record_experience_view_invocation_action",
                                "endpoint_ref": "experience.record_experience_view_invocation_action.record_experience_view_invocation_action",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "record_experience_view_invocation_action",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.RecordExperienceViewInvocationActionRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.RecordExperienceViewInvocationActionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.RecordExperienceViewInvocationActionResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.RecordExperienceViewInvocationActionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "record_experience_view_invocation_action",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Request one Experience layout "
                                "transition through Experience -> "
                                "Attention.",
                                "discriminant": "experience.request_experience_layout_transition.request_experience_layout_transition",
                                "endpoint_ref": "experience.request_experience_layout_transition.request_experience_layout_transition",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "request_experience_layout_transition",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.layout_transition.RequestExperienceLayoutTransitionRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.layout_transition.service_operation.RequestExperienceLayoutTransitionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.layout_transition.RequestExperienceLayoutTransitionResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.layout_transition.service_operation.RequestExperienceLayoutTransitionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "request_experience_layout_transition",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve declared Experience role "
                                "policy for one invocation action "
                                "config without authorizing a concrete "
                                "actor.",
                                "discriminant": "experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy",
                                "endpoint_ref": "experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_experience_invocation_action_role_policy",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ResolveExperienceInvocationActionRolePolicyRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ResolveExperienceInvocationActionRolePolicyRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ResolveExperienceInvocationActionRolePolicyResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ResolveExperienceInvocationActionRolePolicyResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "resolve_experience_invocation_action_role_policy",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve a semantic Experience intent "
                                "into config-level Thread-Layout "
                                "targets and evidence.",
                                "discriminant": "experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent",
                                "endpoint_ref": "experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_experience_thread_layout_intent",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.thread_layout_resolution.ResolveExperienceThreadLayoutIntentRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.thread_layout_resolution.service_operation.ResolveExperienceThreadLayoutIntentRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.thread_layout_resolution.ResolveExperienceThreadLayoutIntentResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.thread_layout_resolution.service_operation.ResolveExperienceThreadLayoutIntentResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "resolve_experience_thread_layout_intent",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve actor-specific Experience "
                                "session context over Environment "
                                "session Attention resolution.",
                                "discriminant": "experience.session_context.resolve_experience_session_context",
                                "endpoint_ref": "experience.session_context.resolve_experience_session_context",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_experience_session_context",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_context.ResolveExperienceSessionContextRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_context.service_operation.ResolveExperienceSessionContextRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_context.ResolveExperienceSessionContextResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_context.service_operation.ResolveExperienceSessionContextResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "session_context",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Admit an actor to an Experience "
                                "session and ensure one Experience "
                                "session feature.",
                                "discriminant": "experience.session_handoff.ensure_experience_session_handoff",
                                "endpoint_ref": "experience.session_handoff.ensure_experience_session_handoff",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_experience_session_handoff",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_handoff.EnsureExperienceSessionHandoffRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_handoff.service_operation.EnsureExperienceSessionHandoffRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_handoff.EnsureExperienceSessionHandoffResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_handoff.service_operation.EnsureExperienceSessionHandoffResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read Experience session actor "
                                "admission and session feature lease "
                                "health.",
                                "discriminant": "experience.session_handoff.get_experience_session_handoff_status",
                                "endpoint_ref": "experience.session_handoff.get_experience_session_handoff_status",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_experience_session_handoff_status",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_handoff.GetExperienceSessionHandoffStatusRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_handoff.service_operation.GetExperienceSessionHandoffStatusRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_handoff.GetExperienceSessionHandoffStatusResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_handoff.service_operation.GetExperienceSessionHandoffStatusResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            },
                        ],
                        "name": "session_handoff",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve a consumer read frame over "
                                "actor-specific Experience context and "
                                "shared Environment Attention.",
                                "discriminant": "experience.session_view_frame.resolve_experience_session_view_frame",
                                "endpoint_ref": "experience.session_view_frame.resolve_experience_session_view_frame",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_experience_session_view_frame",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_view_frame.ResolveExperienceSessionViewFrameRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_view_frame.service_operation.ResolveExperienceSessionViewFrameRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_view_frame.ResolveExperienceSessionViewFrameResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_view_frame.service_operation.ResolveExperienceSessionViewFrameResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "session_view_frame",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Commit one ExperienceSession rooted on "
                                "a child Identity Session with explicit "
                                "EnvironmentSession provenance.",
                                "discriminant": "experience.start_experience_session.start_experience_session",
                                "endpoint_ref": "experience.start_experience_session.start_experience_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "start_experience_session",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.StartExperienceSessionRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_commit.service_operation.StartExperienceSessionRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.session_commit.StartExperienceSessionResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.session_commit.service_operation.StartExperienceSessionResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                            }
                        ],
                        "name": "start_experience_session",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read and stream Experience " "section-graph-binding state snapshots.",
                                "discriminant": "experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings",
                                "endpoint_ref": "experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "watch_experience_section_graph_bindings",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.WatchExperienceSectionGraphBindingsRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.WatchExperienceSectionGraphBindingsRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.section_graph_binding.WatchExperienceSectionGraphBindingsResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.service_operation.WatchExperienceSectionGraphBindingsResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed "
                                    "Experience "
                                    "section-graph-binding "
                                    "snapshots.",
                                    "events": [
                                        {
                                            "class_ref": "aware_experience_service_dto.experience.section_graph_binding.ExperienceSectionGraphBindingStateEvent",
                                            "kind": "snapshot",
                                            "python_model_ref": "aware_experience_service_dto.experience.section_graph_binding.models.ExperienceSectionGraphBindingStateEvent",
                                            "source_path": "bindings/experience.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/experience.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_experience_section_graph_bindings",
                        "source_path": "bindings/experience.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read and stream Experience-owned "
                                "view-state snapshots for one mounted "
                                "view subscription.",
                                "discriminant": "experience.watch_experience_view_state.watch_experience_view_state",
                                "endpoint_ref": "experience.watch_experience_view_state.watch_experience_view_state",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "watch_experience_view_state",
                                "request": {
                                    "class_ref": "aware_experience_service_dto.experience.view_state.WatchExperienceViewStateRequest",
                                    "python_model_ref": "aware_experience_service_dto.experience.view_state.service_operation.WatchExperienceViewStateRequest",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_experience_service_dto.experience.view_state.WatchExperienceViewStateResponse",
                                    "python_model_ref": "aware_experience_service_dto.experience.view_state.service_operation.WatchExperienceViewStateResponse",
                                    "source_path": "bindings/experience.apis.aware",
                                },
                                "source_path": "bindings/experience.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed " "Experience view-state " "snapshots.",
                                    "events": [
                                        {
                                            "class_ref": "aware_experience_service_dto.experience.view_state.ExperienceViewStateEvent",
                                            "kind": "snapshot",
                                            "python_model_ref": "aware_experience_service_dto.experience.view_state.models.ExperienceViewStateEvent",
                                            "source_path": "bindings/experience.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/experience.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_experience_view_state",
                        "source_path": "bindings/experience.apis.aware",
                    },
                ],
                "name": "experience",
                "source_path": "bindings/experience.apis.aware",
            }
        ],
        "fqn_prefix": "aware_experience_service_api",
        "package_name": "experience-service-api",
        "schema_version": 1,
    }
)

EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF: Final[
    str
] = "experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding"
EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_ENDPOINT_REF: Final[
    str
] = "experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding"
EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_ENDPOINT_REF: Final[str] = (
    "experience.actor_admission.admit_experience_actor_config"
)
EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF: Final[str] = (
    "experience.apply_experience_view_event_transition.apply_experience_view_event_transition"
)
EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_ENDPOINT_REF: Final[str] = (
    "experience.describe_experience_session.describe_experience_session"
)
EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_ENDPOINT_REF: Final[str] = (
    "experience.environment_profile.apply_experience_environment_profile_programs"
)
EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF: Final[str] = (
    "experience.environment_profile.provision_experience_environment_profile"
)
EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF: Final[str] = (
    "experience.environment_profile.upsert_experience_environment_profile"
)
EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF: (
    Final[str]
) = ("experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog")
EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF: Final[
    str
] = "experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state"
EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF: (
    Final[str]
) = ("experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog")
EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_ENDPOINT_REF: Final[
    str
] = "experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state"
EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF: Final[
    str
] = "experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action"
EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_ENDPOINT_REF: Final[str] = (
    "experience.mount_experience_session_profile.mount_experience_session_profile"
)
EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_ENDPOINT_REF: Final[str] = (
    "experience.package_materialization.resolve_experience_package_projection_ownership"
)
EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_ENDPOINT_REF: Final[str] = "experience.program.apply_program_ref"
EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_ENDPOINT_REF: Final[str] = "experience.program.get_turn_execution"
EXPERIENCE__PROGRAM__RUN_PROGRAM_ENDPOINT_REF: Final[str] = "experience.program.run_program"
EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_ENDPOINT_REF: Final[str] = "experience.program.submit_program_turn"
EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF: Final[
    str
] = "experience.record_experience_view_invocation_action.record_experience_view_invocation_action"
EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_ENDPOINT_REF: Final[str] = (
    "experience.request_experience_layout_transition.request_experience_layout_transition"
)
EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_ENDPOINT_REF: Final[
    str
] = "experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy"
EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_ENDPOINT_REF: Final[
    str
] = "experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent"
EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF: Final[str] = (
    "experience.session_context.resolve_experience_session_context"
)
EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF: Final[str] = (
    "experience.session_handoff.ensure_experience_session_handoff"
)
EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF: Final[str] = (
    "experience.session_handoff.get_experience_session_handoff_status"
)
EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF: Final[str] = (
    "experience.session_view_frame.resolve_experience_session_view_frame"
)
EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_ENDPOINT_REF: Final[str] = (
    "experience.start_experience_session.start_experience_session"
)
EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF: Final[
    str
] = "experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings"
EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF: Final[str] = (
    "experience.watch_experience_view_state.watch_experience_view_state"
)

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding": EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF,
    "experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding": EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_ENDPOINT_REF,
    "experience.actor_admission.admit_experience_actor_config": EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_ENDPOINT_REF,
    "experience.apply_experience_view_event_transition.apply_experience_view_event_transition": EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF,
    "experience.describe_experience_session.describe_experience_session": EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_ENDPOINT_REF,
    "experience.environment_profile.apply_experience_environment_profile_programs": EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_ENDPOINT_REF,
    "experience.environment_profile.provision_experience_environment_profile": EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    "experience.environment_profile.upsert_experience_environment_profile": EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    "experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog": EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
    "experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state": EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF,
    "experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog": EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
    "experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state": EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_ENDPOINT_REF,
    "experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action": EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF,
    "experience.mount_experience_session_profile.mount_experience_session_profile": EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_ENDPOINT_REF,
    "experience.package_materialization.resolve_experience_package_projection_ownership": EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_ENDPOINT_REF,
    "experience.program.apply_program_ref": EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_ENDPOINT_REF,
    "experience.program.get_turn_execution": EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_ENDPOINT_REF,
    "experience.program.run_program": EXPERIENCE__PROGRAM__RUN_PROGRAM_ENDPOINT_REF,
    "experience.program.submit_program_turn": EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_ENDPOINT_REF,
    "experience.record_experience_view_invocation_action.record_experience_view_invocation_action": EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF,
    "experience.request_experience_layout_transition.request_experience_layout_transition": EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_ENDPOINT_REF,
    "experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy": EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_ENDPOINT_REF,
    "experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent": EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_ENDPOINT_REF,
    "experience.session_context.resolve_experience_session_context": EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF,
    "experience.session_handoff.ensure_experience_session_handoff": EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF,
    "experience.session_handoff.get_experience_session_handoff_status": EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF,
    "experience.session_view_frame.resolve_experience_session_view_frame": EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF,
    "experience.start_experience_session.start_experience_session": EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_ENDPOINT_REF,
    "experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings": EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF,
    "experience.watch_experience_view_state.watch_experience_view_state": EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF",
    "EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_ENDPOINT_REF",
    "EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_ENDPOINT_REF",
    "EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF",
    "EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_ENDPOINT_REF",
    "EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_ENDPOINT_REF",
    "EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF",
    "EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF",
    "EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF",
    "EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF",
    "EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF",
    "EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_ENDPOINT_REF",
    "EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF",
    "EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_ENDPOINT_REF",
    "EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_ENDPOINT_REF",
    "EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_ENDPOINT_REF",
    "EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_ENDPOINT_REF",
    "EXPERIENCE__PROGRAM__RUN_PROGRAM_ENDPOINT_REF",
    "EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_ENDPOINT_REF",
    "EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF",
    "EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_ENDPOINT_REF",
    "EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_ENDPOINT_REF",
    "EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_ENDPOINT_REF",
    "EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF",
    "EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF",
    "EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF",
    "EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF",
    "EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_ENDPOINT_REF",
    "EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF",
    "EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF",
]
