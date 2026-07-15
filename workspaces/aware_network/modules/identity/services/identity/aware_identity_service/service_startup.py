from __future__ import annotations

import asyncio

from aware_environment_sdk import (
    EnvironmentCommitReceiptSdkClient,
    EnvironmentCommitReceiptSource,
    EnvironmentSdkCommitReceiptSource,
)
from aware_utils.logging import logger

from .environment_fanout import (
    IdentityActorCommitEnvironmentAuthority,
    IdentityActorCommitEnvironmentFanoutConsumer,
    IdentityActorCommitFanoutOutcome,
)

_BACKGROUND_ACTOR_COMMIT_FANOUT_TASKS: set[
    asyncio.Task[tuple[IdentityActorCommitFanoutOutcome, ...]]
] = set()


async def start_identity_actor_commit_environment_fanout(
    *,
    environment_commit_source: EnvironmentCommitReceiptSource | None = None,
    environment_api_client: EnvironmentCommitReceiptSdkClient | None = None,
    authority: IdentityActorCommitEnvironmentAuthority | None = None,
    max_receipts: int | None = None,
) -> object | None:
    if environment_commit_source is None and environment_api_client is not None:
        environment_commit_source = EnvironmentSdkCommitReceiptSource(
            client=environment_api_client,
        )
    if environment_commit_source is None:
        logger.warning(
            "Identity ActorCommit fanout not started; Environment SDK commit "
            "receipt source is unavailable."
        )
        return None
    if authority is None:
        logger.warning(
            "Identity ActorCommit fanout not started; Identity materialization "
            "authority is unavailable."
        )
        return None

    consumer = IdentityActorCommitEnvironmentFanoutConsumer(
        source=environment_commit_source,
        authority=authority,
    )
    if max_receipts is None:
        _track_background_actor_commit_fanout_task(
            asyncio.create_task(
                consumer.run(),
                name="identity-actor-commit-environment-fanout",
            )
        )
        return consumer

    await consumer.run(max_receipts=max_receipts)
    return consumer


def _track_background_actor_commit_fanout_task(
    task: asyncio.Task[tuple[IdentityActorCommitFanoutOutcome, ...]],
) -> None:
    _BACKGROUND_ACTOR_COMMIT_FANOUT_TASKS.add(task)
    task.add_done_callback(_on_background_actor_commit_fanout_done)


def _on_background_actor_commit_fanout_done(
    task: asyncio.Task[tuple[IdentityActorCommitFanoutOutcome, ...]],
) -> None:
    _BACKGROUND_ACTOR_COMMIT_FANOUT_TASKS.discard(task)
    if task.cancelled():
        return
    try:
        task.result()
    except Exception as exc:
        logger.warning("Identity ActorCommit Environment fanout stopped: %s", exc)


__all__ = [
    "start_identity_actor_commit_environment_fanout",
]
