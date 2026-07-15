from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from aware_experience.reactivity_transition_dispatcher import (
    ExperienceViewTransitionApplier,
    ReactivityTransitionSdk,
)
from aware_experience.reactivity_transition_specs import (
    ExperienceReactivityViewTransitionSpecResolution,
)
from aware_experience.reactivity_transition_supervisor import (
    ExperienceReactivityTransitionSupervisorConfig,
    run_experience_reactivity_transition_supervisor,
)
from aware_experience.section_graph_binding.service import apply_view_event_transition
from aware_experience.supervisor.manager import (
    ExperienceSessionFeatureLease,
    ExperienceSessionFeatureRunResult,
)

REACTIVITY_TRANSITION_DISPATCH_FEATURE = "reactivity_transition_dispatch"

TransitionSpecLoader = Callable[
    [],
    Awaitable[ExperienceReactivityViewTransitionSpecResolution],
]
TransitionSpecLoaderFactory = Callable[
    [ExperienceSessionFeatureLease],
    TransitionSpecLoader,
]
HostContextFactory = Callable[[ExperienceSessionFeatureLease], Any]
ReactivitySdkFactory = Callable[[ExperienceSessionFeatureLease], ReactivityTransitionSdk]


@dataclass(frozen=True, slots=True)
class ExperienceReactivityTransitionDispatchFeatureAdapter:
    load_specs_for_lease: TransitionSpecLoaderFactory
    sdk: ReactivityTransitionSdk | None = None
    host_context: Any | None = None
    sdk_for_lease: ReactivitySdkFactory | None = None
    host_context_for_lease: HostContextFactory | None = None
    apply_transition: ExperienceViewTransitionApplier = apply_view_event_transition
    feature_key: str = REACTIVITY_TRANSITION_DISPATCH_FEATURE

    async def run(
        self,
        lease: ExperienceSessionFeatureLease,
    ) -> ExperienceSessionFeatureRunResult:
        sdk = _resolve_sdk(adapter=self, lease=lease)
        host_context = _resolve_host_context(adapter=self, lease=lease)
        config = _supervisor_config_from_lease(lease)
        run = await run_experience_reactivity_transition_supervisor(
            sdk=sdk,
            host_context=host_context,
            load_specs=self.load_specs_for_lease(lease),
            config=config,
            apply_transition=self.apply_transition,
        )
        status = "failed" if run.health.status == "failed" else "completed"
        return ExperienceSessionFeatureRunResult(
            status=status,
            info=run.health.info,
            last_error=run.health.last_error,
            health=run.health,
        )

    async def release(self, lease: ExperienceSessionFeatureLease) -> None:
        return None


def _resolve_sdk(
    *,
    adapter: ExperienceReactivityTransitionDispatchFeatureAdapter,
    lease: ExperienceSessionFeatureLease,
) -> ReactivityTransitionSdk:
    if adapter.sdk_for_lease is not None:
        return adapter.sdk_for_lease(lease)
    if adapter.sdk is None:
        raise RuntimeError(
            "Experience Reactivity transition feature requires a Reactivity SDK."
        )
    return adapter.sdk


def _resolve_host_context(
    *,
    adapter: ExperienceReactivityTransitionDispatchFeatureAdapter,
    lease: ExperienceSessionFeatureLease,
) -> Any:
    if adapter.host_context_for_lease is not None:
        return adapter.host_context_for_lease(lease)
    if adapter.host_context is None:
        raise RuntimeError(
            "Experience Reactivity transition feature requires a host context."
        )
    return adapter.host_context


def _supervisor_config_from_lease(
    lease: ExperienceSessionFeatureLease,
) -> ExperienceReactivityTransitionSupervisorConfig:
    scope = lease.session_scope
    config = lease.config
    subscriber_id = config.get("subscriber_id")
    include_replay = config.get("include_replay", True)
    resume_after_event_id = config.get("resume_after_event_id")
    max_events = config.get("max_events")
    object_instance_graph_id = config.get("object_instance_graph_id")
    return ExperienceReactivityTransitionSupervisorConfig(
        experience_name=scope.experience_name,
        profile_key=scope.profile_key,
        subscriber_id=(
            subscriber_id
            if isinstance(subscriber_id, str) and subscriber_id
            else f"experience.transition.{lease.lease_key}"
        ),
        environment_id_filters=(scope.environment_id,) if scope.environment_id else (),
        branch_filters=(scope.branch_id,) if scope.branch_id else (),
        projection_hash_filters=(scope.projection_hash,) if scope.projection_hash else (),
        object_instance_graph_filters=(
            (cast(UUID, object_instance_graph_id),)
            if isinstance(object_instance_graph_id, UUID)
            else ()
        ),
        include_replay=bool(include_replay),
        resume_after_event_id=(
            cast(UUID, resume_after_event_id)
            if isinstance(resume_after_event_id, UUID)
            else None
        ),
        max_events=max_events if isinstance(max_events, int) else None,
    )


__all__ = [
    "ExperienceReactivityTransitionDispatchFeatureAdapter",
    "HostContextFactory",
    "REACTIVITY_TRANSITION_DISPATCH_FEATURE",
    "ReactivitySdkFactory",
    "TransitionSpecLoader",
    "TransitionSpecLoaderFactory",
]
