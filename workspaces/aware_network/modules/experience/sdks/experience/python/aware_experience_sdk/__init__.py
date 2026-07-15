from __future__ import annotations

from typing import Any

from .client import (
    ExperienceSdkClient,
    build_experience_sdk_client,
)
from aware_experience_service_dto.experience.environment_profile.service_operation import (
    ApplyExperienceEnvironmentProfileProgramsRequest,
    ProvisionExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileRequest,
)
from aware_experience_service_dto.experience.package_materialization.service_operation import (
    ResolveExperiencePackageProjectionOwnershipRequest,
    ResolveExperiencePackageProjectionOwnershipResponse,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
    ExperienceActorConfigRoleAdmissionBinding,
    ExperienceActorConfigRoleEligibility,
)
from aware_experience_service_dto.experience.actor_admission.service_operation import (
    AdmitExperienceActorConfigRequest,
    AdmitExperienceActorConfigResponse,
)
from aware_experience_service_dto.experience.session_handoff.models import (
    ExperienceSessionHandoffActorContext,
    ExperienceSessionHandoffFeatureSpec,
    ExperienceSessionIdentityEvidence,
    ExperienceSessionHandoffReceipt,
    ExperienceSessionHandoffScope,
    ExperienceSessionHandoffStatusReceipt,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionJoinReceipt,
)
from aware_experience_service_dto.experience.session_handoff.service_operation import (
    EnsureExperienceSessionHandoffRequest,
    EnsureExperienceSessionHandoffResponse,
    GetExperienceSessionHandoffStatusRequest,
    GetExperienceSessionHandoffStatusResponse,
)
from aware_experience_service_dto.experience.session_context.models import (
    ExperienceSessionAttentionResolutionRequest,
    ExperienceSessionContextReceipt,
    ExperienceSessionLensContext,
)
from aware_experience_service_dto.experience.session_context.service_operation import (
    ResolveExperienceSessionContextRequest,
    ResolveExperienceSessionContextResponse,
)
from aware_experience_service_dto.experience.session_view_frame.models import (
    ExperienceSessionViewFrame,
    ExperienceSessionViewFrameLens,
)
from aware_experience_service_dto.experience.session_view_frame.service_operation import (
    ResolveExperienceSessionViewFrameRequest,
    ResolveExperienceSessionViewFrameResponse,
)
from aware_experience_service_dto.experience.session_commit.service_operation import (
    MountExperienceSessionProfileRequest,
    MountExperienceSessionProfileResponse,
    StartExperienceSessionRequest,
    StartExperienceSessionResponse,
)
from aware_experience_service_dto.experience.layout_transition.service_operation import (
    RequestExperienceLayoutTransitionRequest,
)
from aware_experience_service_dto.experience.section_graph_binding.models import (
    ExperienceLayoutGraphBindingDescriptor,
    ExperienceLayoutGraphBindingState,
    ExperienceLayoutGraphBindingStateSnapshot,
    ExperienceSectionGraphBindingDescriptor,
    ExperienceSectionGraphBindingState,
    ExperienceSectionGraphBindingStateEvent,
    ExperienceSectionGraphBindingStateSnapshot,
    ExperienceSectionViewResolution,
    ExperienceViewInvocationActionApiDispatchReceipt,
    ExperienceViewInvocationActionDescriptor,
    ExperienceViewInvocationActionReceipt,
)
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceLayoutGraphBindingRequest,
    ActivateExperienceLayoutGraphBindingResponse,
    ActivateExperienceSectionGraphBindingRequest,
    ActivateExperienceSectionGraphBindingResponse,
    ApplyExperienceViewEventTransitionRequest,
    ApplyExperienceViewEventTransitionResponse,
    GetExperienceLayoutGraphBindingCatalogRequest,
    GetExperienceLayoutGraphBindingCatalogResponse,
    GetExperienceLayoutGraphBindingStateRequest,
    GetExperienceLayoutGraphBindingStateResponse,
    GetExperienceSectionGraphBindingCatalogRequest,
    GetExperienceSectionGraphBindingCatalogResponse,
    GetExperienceSectionGraphBindingStateRequest,
    GetExperienceSectionGraphBindingStateResponse,
    InvokeExperienceViewInvocationActionRequest,
    InvokeExperienceViewInvocationActionResponse,
    RecordExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionResponse,
    WatchExperienceSectionGraphBindingsRequest,
    WatchExperienceSectionGraphBindingsResponse,
)
from aware_experience_service_dto.experience.thread_layout_resolution.service_operation import (
    ResolveExperienceThreadLayoutIntentRequest,
)
from aware_experience_service_dto.experience.view_state.models import (
    ExperienceViewStateEvent,
    ExperienceViewStateProviderProvenance,
    ExperienceViewStateSnapshot,
)
from aware_experience_service_dto.experience.view_state.service_operation import (
    WatchExperienceViewStateRequest,
    WatchExperienceViewStateResponse,
)

_LAZY_EXPORTS = {
    "LocalExperienceServiceHostConfig": (
        "aware_experience_sdk.local_host",
        "LocalExperienceServiceHostConfig",
    ),
    "LocalExperienceServiceApiDependencyRouteInstallResult": (
        "aware_experience_sdk.local_host",
        "LocalExperienceServiceApiDependencyRouteInstallResult",
    ),
    "build_local_experience_sdk_client": (
        "aware_experience_sdk.local_host",
        "build_local_experience_sdk_client",
    ),
    "build_local_experience_service_host_api_client": (
        "aware_experience_sdk.local_host",
        "build_local_experience_service_host_api_client",
    ),
    "resolve_local_experience_service_host_config": (
        "aware_experience_sdk.local_host",
        "resolve_local_experience_service_host_config",
    ),
    "install_local_experience_service_api_dependency_routes": (
        "aware_experience_sdk.local_host",
        "install_local_experience_service_api_dependency_routes",
    ),
    "resolve_local_experience_service_api_dependency_routes": (
        "aware_experience_sdk.local_host",
        "resolve_local_experience_service_api_dependency_routes",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module 'aware_experience_sdk' has no attribute {name!r}")
    module_name, attr_name = target
    from importlib import import_module

    return getattr(import_module(module_name), attr_name)


__all__ = [
    "ActivateExperienceLayoutGraphBindingRequest",
    "ActivateExperienceLayoutGraphBindingResponse",
    "ActivateExperienceSectionGraphBindingRequest",
    "ActivateExperienceSectionGraphBindingResponse",
    "AdmitExperienceActorConfigRequest",
    "AdmitExperienceActorConfigResponse",
    "ApplyExperienceEnvironmentProfileProgramsRequest",
    "ApplyExperienceViewEventTransitionRequest",
    "ApplyExperienceViewEventTransitionResponse",
    "MountExperienceSessionProfileRequest",
    "MountExperienceSessionProfileResponse",
    "StartExperienceSessionRequest",
    "StartExperienceSessionResponse",
    "EnsureExperienceSessionHandoffRequest",
    "EnsureExperienceSessionHandoffResponse",
    "ExperienceLayoutGraphBindingDescriptor",
    "ExperienceLayoutGraphBindingState",
    "ExperienceLayoutGraphBindingStateSnapshot",
    "ExperienceSectionGraphBindingDescriptor",
    "ExperienceSectionGraphBindingState",
    "ExperienceSectionGraphBindingStateEvent",
    "ExperienceSectionGraphBindingStateSnapshot",
    "ExperienceSectionViewResolution",
    "ExperienceActorConfigAdmissionReceipt",
    "ExperienceActorConfigRoleAdmissionBinding",
    "ExperienceActorConfigRoleEligibility",
    "EnvironmentActorAdmissionReceipt",
    "EnvironmentSessionJoinReceipt",
    "ExperienceSessionHandoffActorContext",
    "ExperienceSessionHandoffFeatureSpec",
    "ExperienceSessionIdentityEvidence",
    "ExperienceSessionHandoffReceipt",
    "ExperienceSessionHandoffScope",
    "ExperienceSessionHandoffStatusReceipt",
    "ExperienceSessionAttentionResolutionRequest",
    "ExperienceSessionContextReceipt",
    "ExperienceSdkClient",
    "ExperienceSessionLensContext",
    "ExperienceSessionViewFrame",
    "ExperienceSessionViewFrameLens",
    "ExperienceViewInvocationActionApiDispatchReceipt",
    "ExperienceViewInvocationActionDescriptor",
    "ExperienceViewInvocationActionReceipt",
    "ExperienceViewStateEvent",
    "ExperienceViewStateProviderProvenance",
    "ExperienceViewStateSnapshot",
    "GetExperienceSessionHandoffStatusRequest",
    "GetExperienceSessionHandoffStatusResponse",
    "GetExperienceLayoutGraphBindingCatalogRequest",
    "GetExperienceLayoutGraphBindingCatalogResponse",
    "GetExperienceLayoutGraphBindingStateRequest",
    "GetExperienceLayoutGraphBindingStateResponse",
    "GetExperienceSectionGraphBindingCatalogRequest",
    "GetExperienceSectionGraphBindingCatalogResponse",
    "GetExperienceSectionGraphBindingStateRequest",
    "GetExperienceSectionGraphBindingStateResponse",
    "InvokeExperienceViewInvocationActionRequest",
    "InvokeExperienceViewInvocationActionResponse",
    "ProvisionExperienceEnvironmentProfileRequest",
    "RecordExperienceViewInvocationActionRequest",
    "RecordExperienceViewInvocationActionResponse",
    "RequestExperienceLayoutTransitionRequest",
    "ResolveExperienceSessionContextRequest",
    "ResolveExperienceSessionContextResponse",
    "ResolveExperienceSessionViewFrameRequest",
    "ResolveExperienceSessionViewFrameResponse",
    "ResolveExperiencePackageProjectionOwnershipRequest",
    "ResolveExperiencePackageProjectionOwnershipResponse",
    "ResolveExperienceThreadLayoutIntentRequest",
    "UpsertExperienceEnvironmentProfileRequest",
    "WatchExperienceSectionGraphBindingsRequest",
    "WatchExperienceSectionGraphBindingsResponse",
    "WatchExperienceViewStateRequest",
    "WatchExperienceViewStateResponse",
    "build_experience_sdk_client",
    *_LAZY_EXPORTS.keys(),
]
