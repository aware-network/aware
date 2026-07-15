from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from aware_experience.reactivity_transition_specs import (
    resolve_reactivity_view_transition_specs,
)
from aware_experience.section_graph_binding.service import (
    EXPERIENCE_TRANSITION_SPEC_PROJECTION_NAMES,
    hydrate_experience_reference_session,
)
from aware_experience.supervisor import (
    ActionIntentDispatcherFactory,
    ExperienceReactivityActionDispatchFeatureAdapter,
    ExperienceReactivityTransitionDispatchFeatureAdapter,
    ExperienceSessionFeatureLease,
    ExperienceSessionNarrationEventBuffer,
    ExperienceSessionNarrationEventSink,
    ExperienceSessionNarratorFeatureAdapter,
    ExperienceSupervisorManager,
    EXPERIENCE_SESSION_NARRATOR_FEATURE,
    REACTIVITY_TRANSITION_DISPATCH_FEATURE,
    REACTIVITY_ACTION_DISPATCH_FEATURE,
)
from aware_reactivity_sdk import ReactivitySdkClient
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext

from aware_experience_service.reactivity_transition_supervisor import (
    _require_reactivity_sdk,
)
from aware_experience_service.reactivity_action_dispatch_supervisor import (
    CommittedExperienceActionDispatchServiceRuntimeLoader,
    ExperienceActionDispatchServiceRuntimeLoader,
    build_experience_action_intent_dispatcher_factory,
)

HostContextProvider = Callable[[], ServiceApiHostContext]
ReactivitySdkProvider = Callable[[], ReactivitySdkClient]


@dataclass(slots=True)
class _MutableHostContextProvider:
    host_context: ServiceApiHostContext

    def update(self, host_context: ServiceApiHostContext) -> None:
        self.host_context = host_context

    def current(self) -> ServiceApiHostContext:
        return self.host_context


@dataclass(frozen=True, slots=True)
class _SupervisorManagerRecord:
    manager: ExperienceSupervisorManager
    host_context_provider: _MutableHostContextProvider
    narration_event_buffer: ExperienceSessionNarrationEventBuffer


class ExperienceSupervisorManagerHolder:
    def __init__(self) -> None:
        self._records: dict[str, _SupervisorManagerRecord] = {}

    def get_manager(
        self,
        *,
        host_context: ServiceApiHostContext,
        sdk: ReactivitySdkClient | None = None,
    ) -> ExperienceSupervisorManager:
        key = _service_host_key(host_context=host_context)
        record = self._records.get(key)
        if record is not None:
            record.host_context_provider.update(host_context)
            return record.manager

        host_context_provider = _MutableHostContextProvider(host_context)
        narration_event_buffer = ExperienceSessionNarrationEventBuffer()
        manager = build_experience_supervisor_manager(
            host_context_provider=host_context_provider.current,
            sdk=sdk,
            narration_event_sink=narration_event_buffer,
        )
        self._records[key] = _SupervisorManagerRecord(
            manager=manager,
            host_context_provider=host_context_provider,
            narration_event_buffer=narration_event_buffer,
        )
        return manager

    def get_narration_event_buffer(
        self,
        *,
        host_context: ServiceApiHostContext,
        sdk: ReactivitySdkClient | None = None,
    ) -> ExperienceSessionNarrationEventBuffer:
        key = _service_host_key(host_context=host_context)
        record = self._records.get(key)
        if record is None:
            self.get_manager(host_context=host_context, sdk=sdk)
            record = self._records[key]
        else:
            record.host_context_provider.update(host_context)
        return record.narration_event_buffer


def build_experience_supervisor_manager(
    *,
    host_context: ServiceApiHostContext | None = None,
    host_context_provider: HostContextProvider | None = None,
    sdk: ReactivitySdkClient | None = None,
    sdk_provider: ReactivitySdkProvider | None = None,
    narration_event_sink: ExperienceSessionNarrationEventSink | None = None,
    action_intent_dispatcher_for_lease: ActionIntentDispatcherFactory | None = None,
    action_dispatch_runtime_loader: (
        ExperienceActionDispatchServiceRuntimeLoader | None
    ) = None,
) -> ExperienceSupervisorManager:
    resolved_host_context_provider = _resolve_host_context_provider(
        host_context=host_context,
        host_context_provider=host_context_provider,
    )
    resolved_sdk_provider = _resolve_sdk_provider(
        host_context_provider=resolved_host_context_provider,
        sdk=sdk,
        sdk_provider=sdk_provider,
    )
    if (
        action_intent_dispatcher_for_lease is not None
        and action_dispatch_runtime_loader is not None
    ):
        raise ValueError(
            "Experience action dispatch accepts either a dispatcher factory "
            "or runtime loader, not both."
        )
    if (
        action_intent_dispatcher_for_lease is None
        and action_dispatch_runtime_loader is None
    ):
        action_dispatch_runtime_loader = (
            CommittedExperienceActionDispatchServiceRuntimeLoader()
        )
    if action_dispatch_runtime_loader is not None:
        action_intent_dispatcher_for_lease = (
            build_experience_action_intent_dispatcher_factory(
                host_context_provider=resolved_host_context_provider,
                reactivity_sdk_provider=resolved_sdk_provider,
                runtime_loader=action_dispatch_runtime_loader,
            )
        )

    def _load_specs_for_lease(lease: ExperienceSessionFeatureLease):
        async def _load_specs():
            host_context = resolved_host_context_provider()
            session = await hydrate_experience_reference_session(
                host_context=host_context,
                experience_name=lease.session_scope.experience_name,
                projection_names=EXPERIENCE_TRANSITION_SPEC_PROJECTION_NAMES,
            )
            return resolve_reactivity_view_transition_specs(
                session=session,
                experience_name=lease.session_scope.experience_name,
                profile_key=lease.session_scope.profile_key,
            )

        return _load_specs

    reactivity_adapter = ExperienceReactivityTransitionDispatchFeatureAdapter(
        sdk_for_lease=lambda _: cast(Any, resolved_sdk_provider()),
        host_context_for_lease=lambda _: resolved_host_context_provider(),
        load_specs_for_lease=_load_specs_for_lease,
    )
    narrator_adapter = ExperienceSessionNarratorFeatureAdapter(
        receipt_source_for_lease=lambda _: (
            resolved_host_context_provider().environment_commit_receipt_source
        ),
        commit_reader_for_lease=lambda _: (
            resolved_host_context_provider().environment_commit_reader
        ),
        event_sink=narration_event_sink,
    )
    feature_adapters: dict[str, Any] = {
        REACTIVITY_TRANSITION_DISPATCH_FEATURE: reactivity_adapter,
        EXPERIENCE_SESSION_NARRATOR_FEATURE: narrator_adapter,
    }
    if action_intent_dispatcher_for_lease is not None:
        feature_adapters[REACTIVITY_ACTION_DISPATCH_FEATURE] = (
            ExperienceReactivityActionDispatchFeatureAdapter(
                sdk_for_lease=lambda _: cast(Any, resolved_sdk_provider()),
                dispatch_intent_for_lease=action_intent_dispatcher_for_lease,
            )
        )
    return ExperienceSupervisorManager(feature_adapters=feature_adapters)


_DEFAULT_MANAGER_HOLDER = ExperienceSupervisorManagerHolder()


def get_experience_supervisor_manager(
    *,
    host_context: ServiceApiHostContext,
    sdk: ReactivitySdkClient | None = None,
) -> ExperienceSupervisorManager:
    return _DEFAULT_MANAGER_HOLDER.get_manager(host_context=host_context, sdk=sdk)


def get_experience_narration_event_buffer(
    *,
    host_context: ServiceApiHostContext,
    sdk: ReactivitySdkClient | None = None,
) -> ExperienceSessionNarrationEventBuffer:
    return _DEFAULT_MANAGER_HOLDER.get_narration_event_buffer(
        host_context=host_context,
        sdk=sdk,
    )


def _resolve_host_context_provider(
    *,
    host_context: ServiceApiHostContext | None,
    host_context_provider: HostContextProvider | None,
) -> HostContextProvider:
    if host_context_provider is not None:
        return host_context_provider
    if host_context is None:
        raise ValueError(
            "Experience supervisor manager requires a host_context or host_context_provider."
        )
    return lambda: host_context


def _resolve_sdk_provider(
    *,
    host_context_provider: HostContextProvider,
    sdk: ReactivitySdkClient | None,
    sdk_provider: ReactivitySdkProvider | None,
) -> ReactivitySdkProvider:
    if sdk_provider is not None:
        return sdk_provider
    if sdk is not None:
        return lambda: sdk
    return lambda: _require_reactivity_sdk(host_context=host_context_provider())


def _service_host_key(*, host_context: ServiceApiHostContext) -> str:
    return host_context.service_name or "aware_experience"


__all__ = [
    "ExperienceSupervisorManagerHolder",
    "build_experience_supervisor_manager",
    "get_experience_narration_event_buffer",
    "get_experience_supervisor_manager",
]
