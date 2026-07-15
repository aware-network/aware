from __future__ import annotations

import asyncio

from aware_reactivity_sdk.service_host import (
    ReactivityEventDispatcherService,
)
from aware_utils.logging import logger

from .authority import ReactivityServiceAuthority
from .environment_fanout import (
    EnvironmentCommitReceiptSource,
    EnvironmentCommitReceiptSdkClient,
    EnvironmentSdkCommitReceiptSource,
    ReactivityEnvironmentCommitOutcome,
    ReactivityEnvironmentCommitSubscriber,
)

_BACKGROUND_ENVIRONMENT_FANOUT_TASKS: set[
    asyncio.Task[tuple[ReactivityEnvironmentCommitOutcome, ...]]
] = set()


async def start_reactivity_service_dispatcher(
    *,
    environment_commit_source: EnvironmentCommitReceiptSource | None = None,
    environment_api_client: EnvironmentCommitReceiptSdkClient | None = None,
    meta_api_client: object | None = None,
    dispatcher: ReactivityEventDispatcherService | None = None,
    authority: ReactivityServiceAuthority | None = None,
    max_events: int | None = None,
) -> object | None:
    reactivity_dispatcher = dispatcher or ReactivityEventDispatcherService.from_env()
    if reactivity_dispatcher is None:
        return None

    stream_authority = authority or ReactivityServiceAuthority()
    stream_authority.attach_dispatcher(reactivity_dispatcher)

    if environment_commit_source is None and environment_api_client is not None:
        environment_commit_source = EnvironmentSdkCommitReceiptSource(
            client=environment_api_client,
        )

    if environment_commit_source is not None:
        subscriber = ReactivityEnvironmentCommitSubscriber(
            source=environment_commit_source,
            authority=stream_authority,
        )
        if max_events is None:
            _track_background_environment_fanout_task(
                asyncio.create_task(
                    subscriber.run(),
                    name="reactivity-environment-sdk-fanout",
                )
            )
            return stream_authority
        await subscriber.run(max_receipts=max_events)
        return stream_authority

    if meta_api_client is not None:
        logger.warning(
            "Ignoring direct Meta API client for Reactivity startup; Environment "
            "API fanout is the canonical commit source."
        )
        return stream_authority

    logger.warning(
        "Reactivity service dispatcher initialized without Environment commit "
        "fanout source; policy event resolution is not running."
    )
    return stream_authority


def _track_background_environment_fanout_task(
    task: asyncio.Task[tuple[ReactivityEnvironmentCommitOutcome, ...]],
) -> None:
    _BACKGROUND_ENVIRONMENT_FANOUT_TASKS.add(task)
    task.add_done_callback(_on_background_environment_fanout_done)


def _on_background_environment_fanout_done(
    task: asyncio.Task[tuple[ReactivityEnvironmentCommitOutcome, ...]],
) -> None:
    _BACKGROUND_ENVIRONMENT_FANOUT_TASKS.discard(task)
    if task.cancelled():
        return
    try:
        task.result()
    except Exception as exc:
        logger.warning("Reactivity Environment SDK fanout stopped: %s", exc)


__all__ = [
    "start_reactivity_service_dispatcher",
]
