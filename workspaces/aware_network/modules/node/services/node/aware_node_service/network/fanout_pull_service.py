from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID, uuid4

from aware_environment_service_dto.environment.environment import (
    GetLaneHeadRequest,
    GetObjectInstanceGraphCommitRequest,
)
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
)
from aware_network_service_dto.comms.models.network_node import (
    BootEnvironmentDescriptor,
    GetBootEnvironmentDescriptorRequest,
    GetBootEnvironmentDescriptorResponse,
    NetworkNodeOperation,
)
from aware_meta_service.local_sdk import build_local_meta_commit_store
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_network.network.node.manager import network_node_manager
from aware_node_service.control_plane.environment_api_network import (
    build_environment_service_api_client,
    invoke_environment_service_api_request,
)
from aware_node_service.network.fanout_pull_hint_bus import (
    FanoutPullHintBus,
    FanoutPullHintNotification,
)
from aware_utils.logging import logger


@dataclass(frozen=True, slots=True)
class _RemoteBootTarget:
    environment_id: UUID
    process_id: UUID | None
    thread_id: UUID | None


class NetworkFanoutPullService:
    """Node-local receiver for peer fanout pull hints.

    Contract:
    - Subscribe to transport-only `FanoutPullHintBus`.
    - Resolve the remote node's boot environment over the existing node-to-node rail.
    - Fetch the missing remote commit chain for the hinted lane.
    - Append it locally through the Meta SDK commit-store boundary so canonical
      lane-head watchers fire exactly as they do for any other local append path.
    """

    def __init__(self, *, network_router: object) -> None:
        self._network_router = network_router
        self._commit_store = build_local_meta_commit_store()
        self._unsubscribe: Any = None
        self._tasks: set[asyncio.Task[None]] = set()
        self._inflight_lanes: set[tuple[UUID, str]] = set()

    def start(self) -> None:
        if self._unsubscribe is not None:
            return
        self._unsubscribe = FanoutPullHintBus.instance().subscribe_all(
            watcher=self._on_hint
        )
        logger.info("[fanout-pull] NetworkFanoutPullService started")

    async def stop(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        if not self._tasks:
            return
        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _on_hint(self, notification: FanoutPullHintNotification) -> None:
        if (
            notification.source_node_id is None
            or notification.branch_id is None
            or not (notification.projection_hash or "").strip()
        ):
            return

        lane_key = (notification.branch_id, notification.projection_hash.strip())
        if lane_key in self._inflight_lanes:
            return
        self._inflight_lanes.add(lane_key)

        loop = asyncio.get_running_loop()
        task = loop.create_task(self._replicate_from_hint(notification=notification))
        self._tasks.add(task)

        def _cleanup(completed: asyncio.Task[None]) -> None:
            self._tasks.discard(completed)
            self._inflight_lanes.discard(lane_key)

        task.add_done_callback(_cleanup)

    async def _replicate_from_hint(
        self,
        *,
        notification: FanoutPullHintNotification,
    ) -> None:
        branch_id = notification.branch_id
        source_node_id = notification.source_node_id
        projection_hash = (notification.projection_hash or "").strip()
        if branch_id is None or source_node_id is None or not projection_hash:
            return

        try:
            remote_target = await self._fetch_remote_boot_target(
                source_node_id=source_node_id
            )
            remote_head = await self._fetch_remote_lane_head(
                source_node_id=source_node_id,
                remote_target=remote_target,
                branch_id=branch_id,
                projection_hash=projection_hash,
            )
            remote_head_commit_id = remote_head.commit_id or notification.commit_id
            if remote_head_commit_id is None:
                return

            local_head_commit_id = await self._read_local_head_commit_id(
                branch_id=branch_id,
                projection_hash=projection_hash,
            )
            if local_head_commit_id == remote_head_commit_id:
                return

            commits = await self._fetch_missing_remote_commits(
                source_node_id=source_node_id,
                remote_target=remote_target,
                branch_id=branch_id,
                projection_hash=projection_hash,
                remote_head_commit_id=remote_head_commit_id,
                stop_before_commit_id=local_head_commit_id,
            )
            if not commits:
                return

            for commit in reversed(commits):
                await self._append_remote_commit(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit=commit,
                )

            logger.info(
                "[fanout-pull] replicated lane from peer=%s lane=(%s,%s) commits=%s head=%s",
                source_node_id,
                branch_id,
                projection_hash,
                len(commits),
                remote_head_commit_id,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(
                "[fanout-pull] replication failed from peer=%s lane=(%s,%s): %s",
                source_node_id,
                branch_id,
                projection_hash,
                exc,
            )

    async def _read_local_head_commit_id(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> UUID | None:
        head = await self._commit_store.head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if not isinstance(head, dict):
            return None
        raw_commit_id = head.get("commit_id")
        if not isinstance(raw_commit_id, str) or not raw_commit_id.strip():
            return None
        try:
            return UUID(raw_commit_id)
        except Exception:
            return None

    async def _fetch_missing_remote_commits(
        self,
        *,
        source_node_id: UUID,
        remote_target: _RemoteBootTarget,
        branch_id: UUID,
        projection_hash: str,
        remote_head_commit_id: UUID,
        stop_before_commit_id: UUID | None,
    ) -> list[ObjectInstanceGraphCommit]:
        commits: list[ObjectInstanceGraphCommit] = []
        current_commit_id: UUID | None = remote_head_commit_id
        found_local_head = False
        max_commits = int(os.environ.get("AWARE_NODE_FANOUT_PULL_MAX_COMMITS", "256"))

        while current_commit_id is not None:
            commit = await self._fetch_remote_commit(
                source_node_id=source_node_id,
                remote_target=remote_target,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=current_commit_id,
            )
            commits.append(commit)

            parents = tuple(commit.commit.commit_parents)
            parent_commit_id = (
                parents[0].parent_commit_id if len(parents) == 1 else None
            )
            if (
                stop_before_commit_id is not None
                and parent_commit_id == stop_before_commit_id
            ):
                found_local_head = True
                break
            if parent_commit_id is None:
                break

            current_commit_id = parent_commit_id
            if len(commits) >= max_commits:
                raise RuntimeError(
                    "remote commit chain exceeds AWARE_NODE_FANOUT_PULL_MAX_COMMITS "
                    f"(branch_id={branch_id} projection_hash={projection_hash} max={max_commits})"
                )

        if stop_before_commit_id is not None and not found_local_head:
            raise RuntimeError(
                "remote lane head is not a fast-forward of the local lane head "
                f"(branch_id={branch_id} projection_hash={projection_hash} local_head={stop_before_commit_id})"
            )

        return commits

    async def _append_remote_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        await self._commit_store.append(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
            root_object_id=commit.root_source_object_id,
        )

    async def _fetch_remote_boot_target(
        self,
        *,
        source_node_id: UUID,
    ) -> _RemoteBootTarget:
        response = await self._send_remote_network_node_request(
            source_node_id=source_node_id,
            request=GetBootEnvironmentDescriptorRequest(
                actor_id=None,
                node_id=None,
            ),
        )
        if not isinstance(response, GetBootEnvironmentDescriptorResponse):
            raise RuntimeError(
                f"unexpected boot descriptor response type: {type(response)}"
            )
        if (response.status or "").lower() not in {"succeeded", "ready", "running"}:
            raise RuntimeError(
                "remote boot environment descriptor request failed "
                f"(status={response.status} error={response.error})"
            )
        descriptor = response.descriptor
        if not isinstance(descriptor, BootEnvironmentDescriptor):
            raise RuntimeError("remote boot environment descriptor is missing")
        return _RemoteBootTarget(
            environment_id=descriptor.boot_environment_id,
            process_id=descriptor.process_id,
            thread_id=descriptor.thread_id,
        )

    async def _fetch_remote_lane_head(
        self,
        *,
        source_node_id: UUID,
        remote_target: _RemoteBootTarget,
        branch_id: UUID,
        projection_hash: str,
    ) -> object:
        response = await self._send_remote_environment_request(
            source_node_id=source_node_id,
            request=GetLaneHeadRequest(
                actor_id=None,
                environment_id=remote_target.environment_id,
                process_id=remote_target.process_id,
                thread_id=remote_target.thread_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
            ),
        )
        if getattr(response, "operation", None) != "get_lane_head":
            raise RuntimeError(f"unexpected lane head response type: {type(response)}")
        if (response.status or "").lower() not in {"succeeded", "ready", "running"}:
            raise RuntimeError(
                "remote get_lane_head failed "
                f"(status={response.status} error={response.error})"
            )
        return response

    async def _fetch_remote_commit(
        self,
        *,
        source_node_id: UUID,
        remote_target: _RemoteBootTarget,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommit:
        response = await self._send_remote_environment_request(
            source_node_id=source_node_id,
            request=GetObjectInstanceGraphCommitRequest(
                actor_id=None,
                environment_id=remote_target.environment_id,
                process_id=remote_target.process_id,
                thread_id=remote_target.thread_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            ),
        )
        if getattr(response, "operation", None) != "get_object_instance_graph_commit":
            raise RuntimeError(f"unexpected commit response type: {type(response)}")
        if (response.status or "").lower() != "succeeded":
            raise RuntimeError(
                "remote get_object_instance_graph_commit failed "
                f"(commit_id={commit_id} status={response.status} error={response.error})"
            )
        payload = response.commit
        if not isinstance(payload, dict):
            raise RuntimeError(
                f"remote commit payload missing or invalid for commit_id={commit_id}"
            )
        with_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        return ObjectInstanceGraphCommit.model_validate_json(with_json)

    async def _send_remote_network_node_request(
        self,
        *,
        source_node_id: UUID,
        request: object,
    ) -> object:
        response_op = await self._send_remote_request(
            source_node_id=source_node_id,
            network_operation=NetworkOperation(
                id=uuid4(),
                message_type=NetworkOperationMessageType.request,
                type=NetworkOperationType.network_node,
                network_operation_hop_list=[
                    self._build_remote_node_hop(source_node_id)
                ],
                network_node_operation=NetworkNodeOperation(request=cast(Any, request)),
            ),
        )
        response = (
            response_op.network_node_operation.response
            if response_op.network_node_operation is not None
            else None
        )
        if response is None:
            raise RuntimeError(
                "remote node response missing network_node_operation.response"
            )
        return response

    async def _send_remote_environment_request(
        self,
        *,
        source_node_id: UUID,
        request: object,
    ) -> object:
        async def _route_to_environment_service(
            network_op: NetworkOperation,
            *,
            timeout_s: float | None = None,
        ) -> NetworkOperation:
            _ = timeout_s
            return await self._send_remote_request(
                source_node_id=source_node_id,
                network_operation=network_op,
            )

        client = build_environment_service_api_client(
            route_to_environment_service=_route_to_environment_service,
            environment_id=getattr(request, "environment_id"),
            node_id=network_node_manager.hosted_node_id,
            actor_id=getattr(request, "actor_id", None),
        )
        return await invoke_environment_service_api_request(client, request)

    async def _send_remote_request(
        self,
        *,
        source_node_id: UUID,
        network_operation: NetworkOperation,
    ) -> NetworkOperation:
        router = cast(Any, self._network_router)
        external_url = await router._resolve_peer_base_url(
            target_node_id=source_node_id
        )
        return await router._send_request_to_target_node(
            network_operation,
            target_node_id=source_node_id,
            external_url=external_url,
            persist_current_hop=False,
        )

    @staticmethod
    def _build_remote_node_hop(target_node_id: UUID) -> NetworkOperationHop:
        return NetworkOperationHop(
            source_app_type=NetworkAppType.network_node,
            source_node_id=network_node_manager.hosted_node_id,
            target_app_type=NetworkAppType.network_node,
            target_node_id=target_node_id,
        )


__all__ = ["NetworkFanoutPullService"]
