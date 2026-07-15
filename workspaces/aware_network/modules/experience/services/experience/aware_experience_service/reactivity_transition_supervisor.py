from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from aware_experience.reactivity_transition_specs import (
    ExperienceReactivityViewTransitionSpecResolution,
    resolve_reactivity_view_transition_specs,
)
from aware_experience.reactivity_transition_supervisor import (
    ExperienceReactivityTransitionSupervisorConfig,
    ExperienceReactivityTransitionSupervisorRun,
    run_experience_reactivity_transition_supervisor,
)
from aware_experience.section_graph_binding.service import (
    EXPERIENCE_TRANSITION_SPEC_PROJECTION_NAMES,
    hydrate_experience_reference_session,
)
from aware_reactivity_sdk import ReactivitySdkClient
from aware_reactivity_service_api import AwareReactivityServiceApiClient
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)

_REACTIVITY_SERVICE_API_PACKAGE_NAME = "reactivity-service-api"


@dataclass(frozen=True, slots=True)
class ExperienceReactivityTransitionServiceSupervisor:
    host_context: ServiceApiHostContext
    config: ExperienceReactivityTransitionSupervisorConfig
    sdk: ReactivitySdkClient
    load_specs: Callable[
        [],
        Awaitable[ExperienceReactivityViewTransitionSpecResolution],
    ]

    async def run(self) -> ExperienceReactivityTransitionSupervisorRun:
        return await run_experience_reactivity_transition_supervisor(
            sdk=self.sdk,
            host_context=self.host_context,
            load_specs=self.load_specs,
            config=self.config,
        )


def build_experience_reactivity_transition_service_supervisor(
    *,
    host_context: ServiceApiHostContext,
    config: ExperienceReactivityTransitionSupervisorConfig,
    sdk: ReactivitySdkClient | None = None,
) -> ExperienceReactivityTransitionServiceSupervisor:
    resolved_sdk = sdk or _require_reactivity_sdk(host_context=host_context)

    async def _load_specs() -> ExperienceReactivityViewTransitionSpecResolution:
        session = await hydrate_experience_reference_session(
            host_context=host_context,
            experience_name=config.experience_name,
            projection_names=EXPERIENCE_TRANSITION_SPEC_PROJECTION_NAMES,
        )
        return resolve_reactivity_view_transition_specs(
            session=session,
            experience_name=config.experience_name,
            profile_key=config.profile_key,
        )

    return ExperienceReactivityTransitionServiceSupervisor(
        host_context=host_context,
        config=config,
        sdk=resolved_sdk,
        load_specs=_load_specs,
    )


def _require_reactivity_sdk(
    *, host_context: ServiceApiHostContext
) -> ReactivitySdkClient:
    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_REACTIVITY_SERVICE_API_PACKAGE_NAME,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=(
            dict(host_context.invocation_context)
            if host_context.invocation_context is not None
            else None
        ),
    )
    if invoker is None:
        raise RuntimeError(
            "Experience Reactivity transition supervisor requires a Service API "
            "dependency route for reactivity-service-api."
        )
    return ReactivitySdkClient(
        api_client=AwareReactivityServiceApiClient(invoker),
    )


__all__ = [
    "ExperienceReactivityTransitionServiceSupervisor",
    "build_experience_reactivity_transition_service_supervisor",
]
