from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import cast

from aware_utils.logging import logger

from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecycleSubscriptionRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecycleSubscriptionResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishResponse,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveRequest,
)
from aware_reactivity_service_dto.reactivity.action_execution import (
    ReactivityActionExecutionClaimRequest,
    ReactivityActionExecutionClaimResponse,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityEventSubscriptionRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityEventSubscriptionResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivitySemanticEventPublishRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivitySemanticEventPublishResponse,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureRequest,
)
from aware_reactivity_service_dto.reactivity.event_meaning import (
    ReactivityEventMeaningProviderResolveRequest,
    ReactivityEventMeaningProviderResolveResponse,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureResponse,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleListRequest,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleListResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityServiceStatusRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityServiceStatusResponse,
)
from aware_reactivity_service_protocol.protocols import (
    AwareReactivityServiceProtocol,
    ReactivityActionCapabilityServiceProtocol,
    ReactivityActionSubscribeLifecycleStreamEvent,
    ReactivityApiServiceProtocol,
    ReactivityEventCapabilityServiceProtocol,
    ReactivityEventSubscribeEventsStreamEvent,
    ReactivityMeaningCapabilityServiceProtocol,
    ReactivityPolicyCapabilityServiceProtocol,
    ReactivityStatusCapabilityServiceProtocol,
)

from .authority import ReactivityServiceAuthority
from .environment_fanout import (
    EnvironmentCommitReceiptSdkClient,
    EnvironmentSdkCommitReceiptSource,
    ReactivityEnvironmentCommitOutcome,
    ReactivityEnvironmentCommitSubscriber,
)


def build_aware_reactivity_service_protocol_handler(
    *,
    authority: ReactivityServiceAuthority | None = None,
) -> AwareReactivityServiceProtocol:
    return _AwareReactivityServiceProtocolHandler(
        authority=authority or ReactivityServiceAuthority()
    )


class _ReactivityStatusCapabilityHandler:
    def __init__(self, *, authority: ReactivityServiceAuthority) -> None:
        self._authority = authority

    async def get_status(
        self,
        request: ReactivityServiceStatusRequest,
    ) -> ReactivityServiceStatusResponse:
        return await self._authority.get_status(request)


class _ReactivityEventCapabilityHandler:
    def __init__(self, *, authority: ReactivityServiceAuthority) -> None:
        self._authority = authority

    async def subscribe_events(
        self,
        request: ReactivityEventSubscriptionRequest,
    ) -> ReactivityEventSubscriptionResponse:
        return await self._authority.subscribe_events(request)

    async def publish_event(
        self,
        request: ReactivitySemanticEventPublishRequest,
    ) -> ReactivitySemanticEventPublishResponse:
        return await self._authority.publish_semantic_event(request)

    def stream_subscribe_events(
        self,
        request: ReactivityEventSubscriptionRequest,
    ) -> AsyncIterator[ReactivityEventSubscribeEventsStreamEvent]:
        return self._authority.stream_events(request)


class _ReactivityPolicyCapabilityHandler:
    def __init__(self, *, authority: ReactivityServiceAuthority) -> None:
        self._authority = authority

    async def ensure_bundle(
        self,
        request: ReactivityPolicyBundleEnsureRequest,
    ) -> ReactivityPolicyBundleEnsureResponse:
        return await self._authority.ensure_policy_bundle(request)

    async def list_bundles(
        self,
        request: ReactivityPolicyBundleListRequest,
    ) -> ReactivityPolicyBundleListResponse:
        return await self._authority.list_policy_bundles(request)


class _ReactivityMeaningCapabilityHandler:
    def __init__(self, *, authority: ReactivityServiceAuthority) -> None:
        self._authority = authority

    async def resolve_provider_intent(
        self,
        request: ReactivityEventMeaningProviderResolveRequest,
    ) -> ReactivityEventMeaningProviderResolveResponse:
        return await self._authority.resolve_event_meaning_provider_intent(request)


class _ReactivityActionCapabilityHandler:
    def __init__(self, *, authority: ReactivityServiceAuthority) -> None:
        self._authority = authority

    async def subscribe_lifecycle(
        self,
        request: ReactivityActionLifecycleSubscriptionRequest,
    ) -> ReactivityActionLifecycleSubscriptionResponse:
        return await self._authority.subscribe_action_lifecycle(request)

    async def claim_execution(
        self,
        request: ReactivityActionExecutionClaimRequest,
    ) -> ReactivityActionExecutionClaimResponse:
        return await self._authority.claim_action_execution(request)

    async def publish_lifecycle(
        self,
        request: ReactivityActionLifecyclePublishRequest,
    ) -> ReactivityActionLifecyclePublishResponse:
        return await self._authority.publish_action_lifecycle(request)

    async def resolve_intents(
        self,
        request: ReactivityActionIntentResolveRequest,
    ) -> ReactivityActionIntentResolveResponse:
        return await self._authority.resolve_action_intents(request)

    def stream_subscribe_lifecycle(
        self,
        request: ReactivityActionLifecycleSubscriptionRequest,
    ) -> AsyncIterator[ReactivityActionSubscribeLifecycleStreamEvent]:
        return cast(
            AsyncIterator[ReactivityActionSubscribeLifecycleStreamEvent],
            self._authority.stream_action_lifecycle(request),
        )


class _ReactivityApiServiceProtocolHandler:
    def __init__(self, *, authority: ReactivityServiceAuthority) -> None:
        self.action: ReactivityActionCapabilityServiceProtocol = (
            _ReactivityActionCapabilityHandler(authority=authority)
        )
        self.event: ReactivityEventCapabilityServiceProtocol = (
            _ReactivityEventCapabilityHandler(authority=authority)
        )
        self.meaning: ReactivityMeaningCapabilityServiceProtocol = (
            _ReactivityMeaningCapabilityHandler(authority=authority)
        )
        self.policy: ReactivityPolicyCapabilityServiceProtocol = (
            _ReactivityPolicyCapabilityHandler(authority=authority)
        )
        self.status: ReactivityStatusCapabilityServiceProtocol = (
            _ReactivityStatusCapabilityHandler(authority=authority)
        )


class _AwareReactivityServiceProtocolHandler:
    def __init__(self, *, authority: ReactivityServiceAuthority) -> None:
        self._authority = authority
        self._environment_fanout_task: (
            asyncio.Task[tuple[ReactivityEnvironmentCommitOutcome, ...]] | None
        ) = None
        self.reactivity: ReactivityApiServiceProtocol = (
            _ReactivityApiServiceProtocolHandler(authority=authority)
        )

    async def start_service_host(
        self,
        *,
        environment_api_client: EnvironmentCommitReceiptSdkClient | None = None,
    ) -> None:
        if environment_api_client is None:
            self._authority.set_environment_fanout_lifecycle(
                attached=False,
                running=False,
                error="environment_api_client_unavailable",
            )
            logger.warning(
                "Reactivity service hosted without Environment receipt fanout client; "
                "semantic event resolution is inactive."
            )
            return
        if (
            self._environment_fanout_task is not None
            and not self._environment_fanout_task.done()
        ):
            return
        subscriber = ReactivityEnvironmentCommitSubscriber(
            source=EnvironmentSdkCommitReceiptSource(client=environment_api_client),
            authority=self._authority,
        )
        self._environment_fanout_task = asyncio.create_task(
            subscriber.run(),
            name="reactivity-servicehost-environment-fanout",
        )
        self._environment_fanout_task.add_done_callback(
            self._on_environment_fanout_done
        )
        self._authority.set_environment_fanout_lifecycle(
            attached=True,
            running=True,
        )

    async def close_service_host(self) -> None:
        task = self._environment_fanout_task
        self._environment_fanout_task = None
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.warning("Reactivity Environment fanout close failed: %s", exc)
        finally:
            self._authority.set_environment_fanout_lifecycle(
                attached=True,
                running=False,
            )

    def _on_environment_fanout_done(
        self,
        task: asyncio.Task[tuple[ReactivityEnvironmentCommitOutcome, ...]],
    ) -> None:
        if task.cancelled():
            return
        try:
            task.result()
        except Exception as exc:
            self._authority.set_environment_fanout_lifecycle(
                attached=True,
                running=False,
                error=str(exc),
            )
            logger.warning("Reactivity Environment fanout stopped: %s", exc)
        else:
            self._authority.set_environment_fanout_lifecycle(
                attached=True,
                running=False,
                error="environment_fanout_ended",
            )


__all__ = [
    "build_aware_reactivity_service_protocol_handler",
]
