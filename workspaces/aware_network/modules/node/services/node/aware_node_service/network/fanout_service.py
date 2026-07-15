from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from uuid import UUID, uuid4

from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentConfigRequest,
    FetchCapabilitiesRequest,
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
)
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
)
from aware_network_service_dto.comms.models.network_node import NetworkNodeOperation
from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_identity_id,
)
from aware_network.communications.app import NetworkApp
from aware_network.network.node.manager import network_node_manager
from aware_network_ontology.stable_ids import (
    stable_network_node_id,
    stable_network_node_peer_id,
)
from aware_utils.logging import logger

from aware_node_service.control_plane.environment_registry import environment_registry
from aware_node_service.control_plane.environment_api_network import (
    build_environment_service_api_client,
    invoke_environment_service_api_request,
)
from aware_node_service.duplex.lane_commit_receipt_bus import LaneCommitReceiptBus


@dataclass(frozen=True, slots=True)
class FanoutPeer:
    node_id: UUID
    base_url: str


@dataclass(frozen=True, slots=True)
class FanoutLane:
    branch_id: UUID
    projection_hash: str


def _normalize_node_endpoint(endpoint: str) -> str:
    endpoint = (endpoint or "").strip()
    if not endpoint:
        return endpoint

    # Accept http(s) and convert to ws(s) for duplex clients.
    if endpoint.startswith("http://"):
        endpoint = "ws://" + endpoint[len("http://") :]
    elif endpoint.startswith("https://"):
        endpoint = "wss://" + endpoint[len("https://") :]

    # Some operators paste full URLs including duplex paths.
    trimmed = endpoint.rstrip("/")
    for suffix in ("/interface/network_node", "/network_node/network_node"):
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)]
            break
    trimmed = trimmed.rstrip("/")

    # Drop any leftover path/query fragments.
    try:
        parsed = urlparse(trimmed)
        if parsed.scheme and parsed.netloc:
            trimmed = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    except Exception:
        pass

    return trimmed.rstrip("/")


def _read_env_or_file(*, env_var: str, file_env_var: str) -> str:
    raw = (os.environ.get(env_var) or "").strip()
    if raw:
        return raw
    path_raw = (os.environ.get(file_env_var) or "").strip()
    if not path_raw:
        return ""
    return Path(path_raw).expanduser().read_text(encoding="utf-8").strip()


def _parse_peers(payload: object) -> list[FanoutPeer]:
    if not isinstance(payload, list):
        raise ValueError("peer payload must be a JSON list")

    peers: list[FanoutPeer] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        base_url = str(
            item.get("base_url")
            or item.get("http_base_url")
            or item.get("peer_http_base_url")
            or ""
        ).strip()
        if not base_url:
            continue

        node_id_raw = str(item.get("node_id") or "").strip()
        public_key = str(item.get("public_key") or "").strip()

        node_id: UUID | None = None
        if node_id_raw:
            node_id = UUID(node_id_raw)
        elif public_key:
            canonical_key, _key_bytes = canonicalize_ed25519_public_key(public_key)
            node_id = stable_network_node_id(public_key=canonical_key)

        if node_id is None:
            continue

        peers.append(FanoutPeer(node_id=node_id, base_url=base_url))

    return peers


def _parse_lanes(payload: object) -> list[FanoutLane]:
    if not isinstance(payload, list):
        raise ValueError("lane payload must be a JSON list")

    lanes: list[FanoutLane] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        branch_raw = str(item.get("branch_id") or "").strip()
        proj_hash = str(item.get("projection_hash") or "").strip()
        if not branch_raw or not proj_hash:
            continue
        lanes.append(FanoutLane(branch_id=UUID(branch_raw), projection_hash=proj_hash))

    return lanes


class NetworkFanoutService:
    """Node-internal fanout trigger (v0).

    v0 contract:
    - Subscribes to `LaneCommitReceiptBus` (ENV→Node receipt notifications).
    - Filters receipts by explicit lane allowlist.
    - Emits a node↔node notification instructing peers to pull the lane.

    This intentionally does *not* push commits. Peers must pull commits and apply
    them locally (SSOT is still commits; DB is rebuildable index).
    """

    def __init__(
        self,
        *,
        network_app: NetworkApp,
        enabled: bool,
        peers: list[FanoutPeer],
        lanes: list[FanoutLane],
        use_graph_policy: bool = False,
        policy_cache_ttl_s: float = 5.0,
    ) -> None:
        self._network_app = network_app
        self._enabled = enabled
        self._peers = peers
        self._lanes = {(lane.branch_id, lane.projection_hash) for lane in lanes}
        self._use_graph_policy = use_graph_policy
        self._policy_cache_ttl_s = max(policy_cache_ttl_s, 0.5)
        self._policy_cache_expires_at = 0.0
        self._peers_by_lane: dict[tuple[UUID, str], list[FanoutPeer]] = {}
        self._net_meta_loaded = False
        self._net_node_opg_id: UUID | None = None
        self._net_node_projection_hash: str | None = None
        self._list_peers_fn_id: UUID | None = None
        self._refresh_lock = None
        self._unsubscribe = None

    @classmethod
    def from_env(cls, *, network_app: NetworkApp) -> "NetworkFanoutService | None":
        enabled_raw = (
            (os.environ.get("AWARE_NODE_FANOUT_ENABLED") or "").strip().lower()
        )
        enabled = enabled_raw in {"1", "true", "yes"}
        if not enabled:
            return None

        # Preferred v0.1: commit-backed policy (NetworkNodePeer.fanout_rules) via DB-backed reads.
        # Back-compat: explicit env-configured peers + lane allowlist.
        try:
            peers_raw = _read_env_or_file(
                env_var="AWARE_NODE_FANOUT_PEERS_JSON",
                file_env_var="AWARE_NODE_FANOUT_PEERS_FILE",
            )
            peers: list[FanoutPeer] = []
            if peers_raw:
                peers_payload = json.loads(peers_raw)
                peers = _parse_peers(peers_payload)
        except Exception as exc:
            logger.warning("[fanout] failed to parse peers config: %s", exc)
            peers = []

        try:
            lanes_raw = _read_env_or_file(
                env_var="AWARE_NODE_FANOUT_LANES_JSON",
                file_env_var="AWARE_NODE_FANOUT_LANES_FILE",
            )
            lanes: list[FanoutLane] = []
            if lanes_raw:
                lanes_payload = json.loads(lanes_raw)
                lanes = _parse_lanes(lanes_payload)
        except Exception as exc:
            logger.warning("[fanout] failed to parse lanes config: %s", exc)
            lanes = []

        if peers and lanes:
            return cls(
                network_app=network_app,
                enabled=True,
                peers=peers,
                lanes=lanes,
                use_graph_policy=False,
            )

        return cls(
            network_app=network_app,
            enabled=True,
            peers=[],
            lanes=[],
            use_graph_policy=True,
        )

    def start(self) -> None:
        if not self._enabled:
            return

        if self._unsubscribe is not None:
            return

        self._unsubscribe = LaneCommitReceiptBus.instance().subscribe_all(
            watcher=self._on_receipt
        )
        mode = "graph" if self._use_graph_policy else "env"
        logger.info(
            "[fanout] NetworkFanoutService started (mode=%s peers=%d lanes=%d)",
            mode,
            len(self._peers),
            len(self._lanes),
        )

    def stop(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    async def _send_environment_request(
        self,
        *,
        request: object,
        environment_id: UUID,
        timeout_s: float | None = 10.0,
    ) -> object:
        record = environment_registry.get(environment_id)
        if record is None:
            raise RuntimeError(f"[fanout] unknown environment_id: {environment_id}")

        node_id = network_node_manager.hosted_node_id

        async def _route_to_environment_service(
            network_op: NetworkOperation,
            *,
            timeout_s: float | None = None,
        ) -> NetworkOperation:
            duplex = self._network_app.get_duplex_client(NetworkAppType.environment)
            await duplex.ensure_connection(
                connection_id=environment_id,
                external_url=record.environment_endpoint,
            )
            raw = await duplex.send_request(
                connection_id=environment_id,
                data_serialized=network_op.model_dump_json(),
                timeout_s=timeout_s,
            )
            if raw is None:
                raise RuntimeError("[fanout] no response from environment service")
            if isinstance(raw, str):
                return NetworkOperation.model_validate_json(raw)
            if isinstance(raw, dict):
                return NetworkOperation.model_validate(raw)
            raise TypeError(
                f"[fanout] unexpected environment response type: {type(raw)}"
            )

        client = build_environment_service_api_client(
            route_to_environment_service=_route_to_environment_service,
            environment_id=environment_id,
            node_id=node_id,
            actor_id=getattr(request, "actor_id", None),
            default_timeout_s=timeout_s,
        )
        return await invoke_environment_service_api_request(client, request)

    async def _ensure_graph_metadata(self, *, environment_id: UUID) -> None:
        if self._net_meta_loaded:
            return

        if self._refresh_lock is None:
            import asyncio

            self._refresh_lock = asyncio.Lock()

        async with self._refresh_lock:
            if self._net_meta_loaded:
                return

            record = environment_registry.get(environment_id)
            if record is None:
                raise RuntimeError(f"[fanout] unknown environment_id: {environment_id}")
            if record.process_id is None or record.thread_id is None:
                raise RuntimeError(
                    f"[fanout] environment missing process_id/thread_id: {environment_id}"
                )

            desc_req = DescribeEnvironmentConfigRequest(
                actor_id=None,
                environment_id=environment_id,
                process_id=record.process_id,
                thread_id=record.thread_id,
                branch_id=record.branch_id,
                projection_hash=None,
            )
            payload = await self._send_environment_request(
                request=desc_req,
                environment_id=environment_id,
                timeout_s=15.0,
            )
            if getattr(payload, "operation", None) != "describe_environment_config":
                raise RuntimeError(
                    "[fanout] describe_environment_config returned unexpected payload"
                )

            net_node_opg = next(
                (
                    opg
                    for opg in payload.opgs
                    if (opg.name or "").strip() == "NetworkNode"
                ),
                None,
            )
            if net_node_opg is None:
                raise RuntimeError(
                    "[fanout] missing network_node OPG in kernel environment"
                )
            self._net_node_opg_id = net_node_opg.id
            self._net_node_projection_hash = net_node_opg.projection_hash

            caps_req = FetchCapabilitiesRequest(
                actor_id=None,
                environment_id=environment_id,
                process_id=record.process_id,
                thread_id=record.thread_id,
                branch_id=None,
                projection_hash=None,
            )
            caps_payload = await self._send_environment_request(
                request=caps_req,
                environment_id=environment_id,
                timeout_s=15.0,
            )
            if getattr(caps_payload, "operation", None) != "fetch_capabilities":
                raise RuntimeError(
                    "[fanout] fetch_capabilities returned unexpected payload"
                )

            list_peers_fn_id: UUID | None = None
            for obj in caps_payload.objects:
                if obj.name != "NetworkNode":
                    continue
                list_peers_fn_id = next(
                    (fn.id for fn in obj.functions if fn.name == "list_peers"), None
                )
                break
            if list_peers_fn_id is None:
                raise RuntimeError(
                    "[fanout] missing NetworkNode.list_peers in capabilities"
                )
            self._list_peers_fn_id = list_peers_fn_id

            self._net_meta_loaded = True

    async def _refresh_graph_policy(self, *, environment_id: UUID) -> None:
        await self._ensure_graph_metadata(environment_id=environment_id)

        now = time.monotonic()
        if now < self._policy_cache_expires_at:
            return

        if self._refresh_lock is None:
            import asyncio

            self._refresh_lock = asyncio.Lock()

        async with self._refresh_lock:
            now = time.monotonic()
            if now < self._policy_cache_expires_at:
                return

            record = environment_registry.get(environment_id)
            if record is None:
                return
            if record.process_id is None or record.thread_id is None:
                return

            node_id = network_node_manager.hosted_node_id
            invoke_req = InvokeFunctionRequest(
                actor_id=None,
                environment_id=environment_id,
                process_id=record.process_id,
                thread_id=record.thread_id,
                branch_id=node_id,
                projection_hash=(self._net_node_projection_hash or "").strip(),
                call_target=InvokeFunctionCallTarget.instance,
                object_id=node_id,
                object_projection_graph_id=self._net_node_opg_id,
                function_id=self._list_peers_fn_id,
                args=[],
                kwargs={
                    "include_incoming": False,
                    "include_outgoing": True,
                    "limit_results": 500,
                },
                commit=False,
                publish=False,
            )
            resp = await self._send_environment_request(
                request=invoke_req,
                environment_id=environment_id,
                timeout_s=15.0,
            )
            if getattr(resp, "operation", None) != "invoke_function":
                raise RuntimeError(
                    "[fanout] invoke_function(list_peers) returned unexpected payload"
                )
            if (resp.status or "").lower() != "succeeded":
                raise RuntimeError(resp.error or "NetworkNode.list_peers failed")

            payload = resp.payload
            if isinstance(payload, dict) and "value" in payload:
                payload = payload.get("value")
            if not isinstance(payload, dict):
                return
            raw_results = payload.get("results")
            if not isinstance(raw_results, list):
                return

            mapping: dict[tuple[UUID, str], list[FanoutPeer]] = {}
            for item in raw_results:
                if not isinstance(item, dict):
                    continue
                status = str(item.get("status") or "").strip().lower()
                if status != "accepted":
                    continue
                peer_node_id_raw = str(item.get("peer_node_id") or "").strip()
                peer_base_url_raw = str(item.get("peer_http_base_url") or "").strip()
                if not peer_node_id_raw or not peer_base_url_raw:
                    continue
                try:
                    peer_node_id = UUID(peer_node_id_raw)
                except Exception:
                    continue
                peer_base_url = _normalize_node_endpoint(peer_base_url_raw)
                if not peer_base_url:
                    continue

                rules = item.get("fanout_rules")
                if not isinstance(rules, list):
                    continue
                for rule in rules:
                    if not isinstance(rule, dict):
                        continue
                    if not bool(rule.get("enabled", True)):
                        continue
                    lane_branch_raw = str(rule.get("lane_branch_id") or "").strip()
                    lane_hash = str(rule.get("lane_projection_hash") or "").strip()
                    if not lane_branch_raw or not lane_hash:
                        continue
                    try:
                        lane_branch_id = UUID(lane_branch_raw)
                    except Exception:
                        continue
                    key = (lane_branch_id, lane_hash)
                    mapping.setdefault(key, []).append(
                        FanoutPeer(node_id=peer_node_id, base_url=peer_base_url)
                    )

            self._peers_by_lane = mapping
            self._policy_cache_expires_at = time.monotonic() + self._policy_cache_ttl_s

    async def _on_receipt(self, receipt: LaneCommitReceiptNotification) -> None:
        if not self._enabled:
            return
        if receipt.branch_id is None:
            return
        projection_hash = (receipt.projection_hash or "").strip()
        if not projection_hash:
            return

        key: tuple[UUID, str]
        if self._use_graph_policy:
            # v0.1 graph policy keys lanes by meta OIGB id (stable, non-invertible).
            key = (
                stable_object_instance_graph_branch_id(
                    object_instance_graph_identity_id=stable_object_instance_graph_identity_id(
                        branch_id=receipt.branch_id
                    ),
                    branch_id=receipt.branch_id,
                ),
                projection_hash,
            )
        else:
            # v0 env policy keys lanes by the domain lane coordinate.
            key = (receipt.branch_id, projection_hash)
            if key not in self._lanes:
                return

        local_node_id = network_node_manager.hosted_node_id
        duplex = self._network_app.get_duplex_client(NetworkAppType.network_node)

        peers: list[FanoutPeer]
        if self._use_graph_policy:
            env_id = receipt.environment_id
            if env_id is None:
                return
            await self._refresh_graph_policy(environment_id=env_id)
            peers = list(self._peers_by_lane.get(key, []))
            if not peers:
                return
        else:
            peers = list(self._peers)

        for peer in peers:
            try:
                connection_id = stable_network_node_peer_id(
                    source_peer_node_id=local_node_id,
                    target_peer_node_id=peer.node_id,
                )
                await duplex.ensure_connection(
                    connection_id=connection_id, external_url=peer.base_url
                )

                hop = NetworkOperationHop(
                    source_app_type=NetworkAppType.network_node,
                    source_node_id=local_node_id,
                    target_app_type=NetworkAppType.network_node,
                    target_node_id=peer.node_id,
                )

                request_payload: dict[str, object] = {
                    "operation": "fanout_notify_pull",
                    "node_id": str(local_node_id),
                    "environment_id": str(receipt.environment_id),
                    "branch_id": str(receipt.branch_id),
                    "projection_hash": projection_hash,
                    "commit_id": str(receipt.commit_id),
                    "head_version": receipt.head_version,
                    "graph_hash_post": receipt.graph_hash_post,
                }
                if receipt.actor_id is not None:
                    request_payload["actor_id"] = str(receipt.actor_id)

                net_op = NetworkOperation(
                    id=uuid4(),
                    message_type=NetworkOperationMessageType.notification,
                    type=NetworkOperationType.network_node,
                    network_node_operation=NetworkNodeOperation(
                        request=request_payload
                    ),
                    network_operation_hop_list=[hop],
                )

                await duplex.send_notification(
                    connection_id=connection_id,
                    data_serialized=net_op.model_dump_json(),
                )
            except Exception as exc:
                logger.warning(
                    "[fanout] failed to notify peer %s: %s", peer.node_id, exc
                )


__all__ = ["NetworkFanoutService", "FanoutPeer", "FanoutLane"]
