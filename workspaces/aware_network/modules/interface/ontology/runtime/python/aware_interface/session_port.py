from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
import os
import platform
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api.context import AwareApiContext
from aware_attention_ontology.stable_ids import (
    stable_layout_id,
    stable_layout_section_id,
    stable_section_focus_scope_id,
    stable_section_id,
)
from aware_interface_ontology.stable_ids import stable_window_id

from aware_interface.lane_sync import (
    InterfaceLaneSyncSource,
    InterfaceRemoteLaneMaterialization,
)
from aware_interface.session_state import (
    InterfaceRuntimeSessionStateStore,
    PersistedAuthoritySnapshot,
    PersistedEnvironmentSession,
)


_DEFAULT_LAYOUT_KEY = "mobile-conversation-workspace"
_DEFAULT_SECTION_KEY = "workspace"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_endpoint(endpoint: str) -> str:
    return endpoint.strip().rstrip("/")


def _normalize_token(raw: str, *, field_name: str) -> str:
    value = (raw or "").strip().lower()
    if not value:
        raise ValueError(f"{field_name} is required")
    return value


def _projection_lookup_key(raw: str, *, field_name: str) -> str:
    value = (raw or "").strip().casefold()
    if not value:
        raise ValueError(f"{field_name} is required")
    lookup_key = "".join(char for char in value if char.isalnum())
    if not lookup_key:
        raise ValueError(f"{field_name} is required")
    return lookup_key


def _optional_projection_lookup_key(raw: object) -> str | None:
    value = str(raw or "").strip().casefold()
    if not value:
        return None
    lookup_key = "".join(char for char in value if char.isalnum())
    return lookup_key or None


def _normalize_optional_token(raw: Any, *, lower: bool = False) -> str | None:
    value = str(raw or "").strip()
    if not value:
        return None
    if lower:
        return value.lower()
    return value


def _to_jsonable(value: Any) -> Any:
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return dump(mode="json")
    return value


def _resolve_interface_os() -> str:
    raw = (
        os.environ.get("AWARE_INTERFACE_OS") or os.environ.get("AWARE_CLIENT_OS") or ""
    ).strip()
    if raw:
        return raw.lower()
    system = (platform.system() or "").strip().lower()
    if system.startswith("darwin"):
        return "macos"
    if system.startswith("windows"):
        return "windows"
    return "linux"


def _resolve_interface_version() -> str:
    raw = (
        os.environ.get("AWARE_INTERFACE_VERSION")
        or os.environ.get("AWARE_CLIENT_VERSION")
        or ""
    ).strip()
    return raw or "aware-interface"


def _stable_window_id_for_interface(*, interface_id: UUID, window_key: str) -> UUID:
    key_norm = _normalize_token(window_key, field_name="window_key")
    external_window_id = uuid5(
        NAMESPACE_URL,
        f"aware:window:{interface_id}:{key_norm}",
    )
    return stable_window_id(window_id=external_window_id)


def _select_topology_process(
    *,
    processes: tuple[Any, ...],
    process_id: UUID | None,
) -> Any | None:
    if not processes:
        return None
    if process_id is not None:
        for process in processes:
            if getattr(process, "process_id", None) == process_id:
                return process
    return processes[0]


def _select_topology_thread(
    *,
    threads: tuple[Any, ...],
    thread_id: UUID | None,
) -> Any | None:
    if not threads:
        return None
    if thread_id is not None:
        for thread in threads:
            if getattr(thread, "thread_id", None) == thread_id:
                return thread
    return threads[0]


def _ordered_attachments(*, attachments: tuple[Any, ...]) -> tuple[Any, ...]:
    active = tuple(
        attachment
        for attachment in attachments
        if bool(getattr(attachment, "is_active", False))
    )
    if not active:
        return attachments
    inactive = tuple(
        attachment
        for attachment in attachments
        if not bool(getattr(attachment, "is_active", False))
    )
    return active + inactive


def _lane_hash_for_opg(*, lanes: tuple[Any, ...], opg_name: str) -> str | None:
    opg_name_norm = _projection_lookup_key(opg_name, field_name="opg_name")
    for lane in lanes:
        lane_opg_name = _normalize_optional_token(
            getattr(lane, "opg_name", None),
            lower=True,
        )
        lane_hash = _normalize_optional_token(getattr(lane, "lane_hash", None))
        if (
            lane_opg_name is not None
            and _projection_lookup_key(lane_opg_name, field_name="lane.opg_name")
            == opg_name_norm
            and lane_hash is not None
        ):
            return lane_hash
    return None


@dataclass(frozen=True, slots=True)
class InterfaceBootstrapResult:
    context: AwareApiContext
    environment_id: UUID
    environment_config_id: UUID | None
    provision: Any | None
    status: Any | None
    describe_environment_config: Any
    describe_environment: Any
    capabilities: Any


@dataclass(frozen=True, slots=True)
class FocusScopeLane:
    interface_id: UUID
    window_key: str
    window_id: UUID
    focus_scope_id: UUID
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class SectionFocusScopeLane:
    interface_id: UUID
    window_key: str
    layout_key: str
    section_key: str
    window_id: UUID
    layout_id: UUID
    section_id: UUID
    layout_section_id: UUID
    section_focus_scope_id: UUID
    focus_scope_id: UUID
    branch_id: UUID
    projection_hash: str


class InterfaceRuntimeSessionPort:
    """Interface runtime port replacing deprecated AwareSession consumers."""

    def __init__(
        self,
        *,
        client: Any,
        interface_id: UUID,
        endpoint: str,
        state_store: InterfaceRuntimeSessionStateStore,
        boot_program_ref: str = "aware_control:EnsureBootInterfaceGraph",
    ) -> None:
        self._client = client
        self._interface_id = interface_id
        self._endpoint = endpoint
        self._state_store = state_store
        self._projection_hash_cache: dict[tuple[UUID, str], str] = {}
        self._describe_environment_config_cache: Any | None = None
        self._describe_environment_cache: Any | None = None
        self._capabilities_cache: Any | None = None
        self._topology_cache: dict[tuple[str | None, str | None], Any] = {}
        self._topology_focus_scope_lane_cache: dict[
            tuple[str | None, str | None, str],
            tuple[UUID, str] | None,
        ] = {}
        self._boot_program_ref = boot_program_ref

    async def bootstrap(
        self,
        *,
        environment_config_id: UUID | None = None,
        persist: bool = True,
    ) -> InterfaceBootstrapResult:
        actor_id = self._client.config.actor_id
        endpoint = self._client.config.endpoint
        environment_id: UUID | None = None

        persisted = await self._state_store.aload(
            actor_id=actor_id,
            endpoint=endpoint,
        )
        if persisted is not None:
            if environment_config_id is None:
                environment_id = persisted.environment_id
                environment_config_id = persisted.environment_config_id
            elif persisted.environment_config_id == environment_config_id:
                environment_id = persisted.environment_id

        provision: Any | None = None
        status: Any | None = None
        if environment_id is None:
            if environment_config_id is None:
                discovered = await self._client.discover_environment_configs()
                configs = getattr(discovered, "configs", discovered) or []
                if not configs:
                    raise RuntimeError("No environment configs available to provision")
                environment_config_id = configs[0].environment_config_id
            provision = await self._client.provision_environment(
                environment_config_id=environment_config_id,
                eager_ready=True,
            )
            if provision is None:
                raise RuntimeError("Provision response missing")
            context = self._context_from_provision(provision)
            environment_id = context.environment_id
        else:
            status = await self._client.get_environment_status(
                environment_id=environment_id,
            )
            if status is None:
                raise RuntimeError("Environment status response missing")
            context = self._context_from_status(status)
            environment_config_id = (
                environment_config_id or status.environment_config_id
            )

        if persist and environment_id is not None:
            await self._state_store.asave(
                PersistedEnvironmentSession(
                    actor_id=actor_id,
                    endpoint=_normalize_endpoint(endpoint),
                    environment_id=environment_id,
                    environment_config_id=environment_config_id,
                    saved_at=_utc_now(),
                )
            )

        self._client.set_context(context)
        described_config = await self._client.describe_environment_config()
        described = await self._client.describe_environment()
        capabilities = await self._client.fetch_capabilities()
        self._describe_environment_config_cache = described_config
        self._describe_environment_cache = described
        self._capabilities_cache = capabilities

        if persist and environment_id is not None:
            ocg_id = getattr(described_config, "ocg_id", None)
            if environment_config_id is not None and ocg_id is not None:
                await self._state_store.asave_authority_snapshot(
                    PersistedAuthoritySnapshot(
                        actor_id=actor_id,
                        endpoint=_normalize_endpoint(endpoint),
                        environment_config_id=environment_config_id,
                        ocg_id=ocg_id,
                        describe_environment_config=described_config,
                        capabilities=capabilities,
                        saved_at=_utc_now(),
                    )
                )

        return InterfaceBootstrapResult(
            context=context,
            environment_id=environment_id,
            environment_config_id=environment_config_id,
            provision=provision,
            status=status,
            describe_environment_config=described_config,
            describe_environment=described,
            capabilities=capabilities,
        )

    async def ensure_boot_interface_graph(self) -> UUID:
        ctx = self._client.get_context()
        if ctx is None:
            raise RuntimeError(
                "Missing transport context; bootstrap the Interface session port first."
            )
        symbols: dict[str, object] = {
            "plan.interface_id": self._interface_id,
            "plan.os": _resolve_interface_os(),
            "plan.version": _resolve_interface_version(),
        }
        await self._client.apply_program_ref(
            program_ref=self._boot_program_ref,
            symbols=symbols,
            validate_only=False,
            commit=True,
            publish=False,
        )
        return self._interface_id

    async def resolve_projection_hash(self, *, opg_name: str) -> str:
        ctx = self._client.get_context()
        if ctx is None or ctx.environment_id is None:
            raise RuntimeError(
                "Missing environment context; bootstrap the Interface session port first."
            )
        key = (
            ctx.environment_id,
            _projection_lookup_key(opg_name, field_name="opg_name"),
        )
        cached = self._projection_hash_cache.get(key)
        if cached is not None:
            return cached
        desc = self._describe_environment_config_cache
        if desc is None:
            desc = await self._client.describe_environment_config()
            self._describe_environment_config_cache = desc
        opg = next(
            (
                entry
                for entry in getattr(desc, "opgs", ()) or ()
                if _optional_projection_lookup_key(getattr(entry, "name", None))
                == key[1]
            ),
            None,
        )
        if opg is None:
            available = sorted(
                {
                    str(getattr(entry, "name", "") or "").strip().lower()
                    for entry in getattr(desc, "opgs", ()) or ()
                }
            )
            raise RuntimeError(
                f"OPG not found in describe_environment_config: "
                f"opg_name={opg_name!r} available={available}"
            )
        projection_hash = str(getattr(opg, "projection_hash", "") or "").strip()
        if not projection_hash:
            raise RuntimeError(
                "OPG missing projection_hash in describe_environment_config: "
                f"opg_name={opg_name!r}"
            )
        self._projection_hash_cache[key] = projection_hash
        return projection_hash

    async def describe_environment_topology(
        self,
        *,
        process_key: str | None = None,
        thread_key: str | None = None,
    ) -> Any:
        key = (process_key, thread_key)
        cached = self._topology_cache.get(key)
        if cached is not None:
            return cached
        topology = await self._client.describe_environment_topology(
            process_key=process_key,
            thread_key=thread_key,
        )
        self._topology_cache[key] = topology
        return topology

    async def resolve_topology_focus_scope_lane(
        self,
        *,
        process_key: str | None = None,
        thread_key: str | None = None,
        opg_name: str = "FocusScope",
    ) -> tuple[UUID, str] | None:
        opg_name_norm = _projection_lookup_key(opg_name, field_name="opg_name")
        cache_key = (process_key, thread_key, opg_name_norm)
        if cache_key in self._topology_focus_scope_lane_cache:
            return self._topology_focus_scope_lane_cache[cache_key]
        context = self._client.get_context()
        if context is None:
            raise RuntimeError(
                "Missing environment context; bootstrap the Interface session port first."
            )
        topology = await self.describe_environment_topology(
            process_key=process_key,
            thread_key=thread_key,
        )
        process = _select_topology_process(
            processes=tuple(getattr(topology, "processes", ()) or ()),
            process_id=context.process_id,
        )
        if process is None:
            return None
        thread = _select_topology_thread(
            threads=tuple(getattr(process, "threads", ()) or ()),
            thread_id=context.thread_id,
        )
        if thread is None:
            return None
        for attachment in _ordered_attachments(
            attachments=tuple(getattr(thread, "attachments", ()) or ()),
        ):
            branch_id = getattr(
                attachment,
                "domain_branch_id",
                None,
            ) or getattr(attachment, "object_instance_graph_branch_id", None)
            if branch_id is None:
                continue
            lane_hash = _lane_hash_for_opg(
                lanes=tuple(getattr(attachment, "lanes", ()) or ()),
                opg_name=opg_name_norm,
            )
            if lane_hash is None:
                continue
            resolved = (branch_id, lane_hash)
            self._topology_focus_scope_lane_cache[cache_key] = resolved
            return resolved
        self._topology_focus_scope_lane_cache[cache_key] = None
        return None

    async def resolve_section_focus_scope_lane(
        self,
        *,
        window_key: str,
        layout_key: str,
        section_key: str,
    ) -> SectionFocusScopeLane:
        window_key_value = _normalize_token(window_key, field_name="window_key")
        layout_key_value = _normalize_token(layout_key, field_name="layout_key")
        section_key_value = _normalize_token(section_key, field_name="section_key")
        window_id = _stable_window_id_for_interface(
            interface_id=self._interface_id,
            window_key=window_key_value,
        )
        layout_id = stable_layout_id(key=layout_key_value)
        section_id = stable_section_id(key=section_key_value)
        layout_section_id = stable_layout_section_id(
            layout_id=layout_id,
            section_id=section_id,
        )
        topology_lane = None
        try:
            topology_lane = await self.resolve_topology_focus_scope_lane()
        except Exception:
            topology_lane = None
        if topology_lane is not None:
            topology_branch_id, projection_hash = topology_lane
            focus_scope_id = UUID(str(topology_branch_id))
        else:
            focus_scope_id = stable_section_focus_scope_id(
                section_id=section_id,
                focus_scope_id=layout_section_id,
            )
            projection_hash = await self.resolve_projection_hash(opg_name="FocusScope")
        section_focus_scope_id = stable_section_focus_scope_id(
            section_id=section_id,
            focus_scope_id=focus_scope_id,
        )
        return SectionFocusScopeLane(
            interface_id=self._interface_id,
            window_key=window_key_value,
            layout_key=layout_key_value,
            section_key=section_key_value,
            window_id=window_id,
            layout_id=layout_id,
            section_id=section_id,
            layout_section_id=layout_section_id,
            section_focus_scope_id=section_focus_scope_id,
            focus_scope_id=focus_scope_id,
            branch_id=focus_scope_id,
            projection_hash=projection_hash,
        )

    async def resolve_focus_scope_lane(self, *, window_key: str) -> FocusScopeLane:
        section_lane = await self.resolve_section_focus_scope_lane(
            window_key=window_key,
            layout_key=_DEFAULT_LAYOUT_KEY,
            section_key=_DEFAULT_SECTION_KEY,
        )
        return FocusScopeLane(
            interface_id=section_lane.interface_id,
            window_key=section_lane.window_key,
            window_id=section_lane.window_id,
            focus_scope_id=section_lane.focus_scope_id,
            branch_id=section_lane.branch_id,
            projection_hash=section_lane.projection_hash,
        )

    def lane_sync_source(
        self,
        *,
        include_commit_payload: bool = True,
    ) -> InterfaceLaneSyncSource:
        return InterfaceApiLaneSyncSource(
            client=self._client,
            include_commit_payload=include_commit_payload,
        )

    def context_ids(self) -> tuple[UUID | None, UUID | None]:
        context = self._client.get_context()
        if context is None:
            raise RuntimeError("Interface session port is missing context.")
        return (
            getattr(context, "process_id", None),
            getattr(context, "thread_id", None),
        )

    @staticmethod
    def _context_from_provision(provision: Any) -> AwareApiContext:
        env_id = provision.environment_id
        process_id = provision.process_id
        thread_id = provision.thread_id
        if env_id is None or process_id is None or thread_id is None:
            raise RuntimeError(
                "Provision response missing environment/process/thread identifiers"
            )
        return AwareApiContext(
            environment_id=env_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=provision.branch_id,
            projection_hash=None,
        )

    @staticmethod
    def _context_from_status(status: Any) -> AwareApiContext:
        process_id = status.process_id
        thread_id = status.thread_id
        if process_id is None or thread_id is None:
            raise RuntimeError("Environment status missing process/thread identifiers")
        return AwareApiContext(
            environment_id=status.environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=status.branch_id,
            projection_hash=None,
        )


class InterfaceApiLaneSyncSource(InterfaceLaneSyncSource):
    def __init__(
        self,
        *,
        client: Any,
        include_commit_payload: bool = True,
    ) -> None:
        self._client = client
        self._include_commit_payload = include_commit_payload

    async def load_latest(
        self,
        *,
        branch_id: str,
        projection_hash: str,
    ) -> InterfaceRemoteLaneMaterialization | None:
        head = await self._client.get_lane_head(
            branch_id=UUID(str(branch_id)),
            projection_hash=projection_hash,
        )
        commit_id = getattr(head, "commit_id", None)
        if commit_id is None:
            return None
        payload = await self._load_commit_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=str(commit_id),
        )
        return InterfaceRemoteLaneMaterialization(
            branch_id=str(branch_id),
            projection_hash=projection_hash,
            commit_id=str(commit_id),
            graph_hash_post=(str(getattr(head, "graph_hash_post", "") or "") or None),
            object_instance_graph_id=(
                str(getattr(head, "object_instance_graph_id", "") or "") or None
            ),
            root_object_id=str(getattr(head, "root_object_id", "") or "") or None,
            head_version=getattr(head, "head_version", None),
            commit_payload=payload,
        )

    async def load_commit(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        commit_id: str,
    ) -> InterfaceRemoteLaneMaterialization | None:
        payload = await self._load_commit_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if self._include_commit_payload and payload is None:
            return None
        return InterfaceRemoteLaneMaterialization(
            branch_id=str(branch_id),
            projection_hash=projection_hash,
            commit_id=str(commit_id),
            commit_payload=payload,
        )

    async def _load_commit_payload(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        commit_id: str,
    ) -> dict[str, Any] | None:
        if not self._include_commit_payload:
            return None
        response = await self._client.get_object_instance_graph_commit(
            commit_id=UUID(str(commit_id)),
            branch_id=UUID(str(branch_id)),
            projection_hash=projection_hash,
        )
        if str(getattr(response, "status", "") or "").strip().lower() not in {
            "succeeded",
            "success",
            "ok",
        }:
            return None
        commit = getattr(response, "commit", None)
        if isinstance(commit, dict):
            return dict(commit)
        return None

    def watch_lane(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        include_initial: bool = True,
    ) -> AsyncIterator[InterfaceRemoteLaneMaterialization]:
        async def _watch() -> AsyncIterator[InterfaceRemoteLaneMaterialization]:
            if include_initial:
                initial = await self.load_latest(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                )
                if initial is not None:
                    yield initial

        return _watch()


__all__ = [
    "FocusScopeLane",
    "InterfaceApiLaneSyncSource",
    "InterfaceBootstrapResult",
    "InterfaceRuntimeSessionPort",
    "SectionFocusScopeLane",
]
