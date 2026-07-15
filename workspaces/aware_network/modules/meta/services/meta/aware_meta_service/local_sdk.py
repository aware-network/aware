from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from aware_meta.graph.instance.projection_readiness import (
    ProjectionReadinessModes,
    ProjectionReadinessRequirement,
    ProjectionReadinessResult,
    ensure_projection_readiness,
)
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_meta.materialization.executor import MaterializationExecutionError
from aware_meta.receipts.lane_head_receipt_relay import LaneHeadReceiptRelay
from aware_meta.runtime import (
    MetaGraphCommitReceipt as LocalGraphCommitReceipt,
    MetaGraphInvokeFunctionInput as LocalGraphInvokeFunctionInput,
    MetaGraphRuntime as LocalGraphRuntime,
    MetaGraphRuntimeContext as LocalGraphRuntimeContext,
    MetaGraphRuntimeIndexSnapshot as LocalGraphRuntimeIndexSnapshot,
    build_meta_graph_runtime_index_snapshot,
)
from aware_meta_sdk.client import MetaSdkClient, MetaSdkError
from aware_meta_sdk.ontology_proof import (
    OigCommitExpectation,
    assert_oig_commit_matches,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionResponse,
)

from .local_api_client import (
    build_local_meta_commit_store,
    build_local_meta_oig_materializer,
    build_local_meta_service_api_client,
    build_local_meta_service_api_client_for_aware_package_manifests,
    build_local_meta_service_api_session,
    build_local_meta_service_api_session_for_aware_package_manifests,
    build_local_meta_snapshot_store,
    load_local_meta_graph_context,
    materialize_local_meta_lane_oig,
    object_instance_graph_commit_from_payload,
    read_local_meta_api_activation_read_model,
    read_local_meta_runtime_read_model,
)


GraphContextSdkFactory = Callable[[object], MetaSdkClient]
build_local_meta_runtime_index_snapshot = build_meta_graph_runtime_index_snapshot


@dataclass(frozen=True, slots=True)
class LocalMetaLaneHead:
    """Committed lane-head coordinates exposed at the local Meta service boundary."""

    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    graph_hash_post: str | None = None
    object_instance_graph_id: UUID | None = None
    root_object_id: UUID | None = None
    version: int | None = None

    def as_mapping(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "branch_id": self.branch_id,
            "projection_hash": self.projection_hash,
            "commit_id": self.commit_id,
        }
        if self.graph_hash_post is not None:
            payload["graph_hash_post"] = self.graph_hash_post
        if self.object_instance_graph_id is not None:
            payload["object_instance_graph_id"] = self.object_instance_graph_id
        if self.root_object_id is not None:
            payload["root_object_id"] = self.root_object_id
        if self.version is not None:
            payload["v"] = self.version
        return payload


@dataclass(frozen=True, slots=True)
class LocalMetaLaneStore:
    """Pythonic local lane facade backed by service-owned Meta stores."""

    _commits: object = field(repr=False)
    _snapshots: object | None = field(default=None, repr=False)
    _materializer: object | None = field(default=None, repr=False)

    async def head(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> LocalMetaLaneHead | None:
        reader = getattr(self._commits, "head", None)
        if not callable(reader):
            raise TypeError("Local Meta lane store commit backend must expose head().")
        raw = await _await_maybe(
            reader(branch_id=branch_id, projection_hash=projection_hash)
        )
        if not isinstance(raw, Mapping):
            return None
        return _local_lane_head_from_mapping(
            branch_id=branch_id,
            projection_hash=projection_hash,
            payload=raw,
        )

    async def get_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> object | None:
        reader = getattr(self._commits, "get_commit", None)
        if not callable(reader):
            raise TypeError(
                "Local Meta lane store commit backend must expose get_commit()."
            )
        return await _await_maybe(
            reader(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
        )

    async def append(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: object,
        root_object_id: UUID | None = None,
        commit_action: object | None = None,
    ) -> Mapping[str, int]:
        writer = getattr(self._commits, "append", None)
        if not callable(writer):
            raise TypeError(
                "Local Meta lane store commit backend must expose append()."
            )
        result = await _await_maybe(
            writer(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit=commit,
                root_object_id=root_object_id,
                commit_action=commit_action,
            )
        )
        if isinstance(result, Mapping):
            return cast(Mapping[str, int], result)
        return {}

    async def materialize(
        self,
        *,
        branch_id: UUID,
        ocg: object,
        opg: object,
        commit_id: UUID | None,
        oig_id: UUID | None = None,
        attribute_configs_by_id: Mapping[UUID, object] | None = None,
        class_configs_by_id: Mapping[UUID, object] | None = None,
        timings: object | None = None,
    ) -> object:
        return await materialize_local_meta_lane_oig(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=commit_id,
            oig_id=oig_id,
            attribute_configs_by_id=attribute_configs_by_id,
            class_configs_by_id=class_configs_by_id,
            timings=timings,
            commits=self._commits,
            snapshots=self._snapshots,
            materializer=self._materializer,
        )

    async def materialize_head(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        ocg: object,
        opg: object,
        attribute_configs_by_id: Mapping[UUID, object] | None = None,
        class_configs_by_id: Mapping[UUID, object] | None = None,
        timings: object | None = None,
    ) -> object | None:
        head = await self.head(branch_id=branch_id, projection_hash=projection_hash)
        if head is None:
            return None
        return await self.materialize(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=head.commit_id,
            oig_id=head.object_instance_graph_id,
            attribute_configs_by_id=attribute_configs_by_id,
            class_configs_by_id=class_configs_by_id,
            timings=timings,
        )


@dataclass(frozen=True, slots=True)
class LocalMetaLaneHeadReceiptRelay:
    """Handle for local lane-head receipt relay lifecycle."""

    _relay: object = field(repr=False)

    def stop(self) -> None:
        stopper = getattr(self._relay, "stop", None)
        if callable(stopper):
            stopper()


@dataclass(frozen=True, slots=True)
class MetaSdkLaneStore:
    """Meta SDK facade for local lane head and commit reads."""

    sdk: MetaSdkClient
    actor_id: UUID | None = None

    async def head(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> Mapping[str, object] | None:
        response = await self.sdk.get_lane_head(
            actor_id=self.actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
        )
        if str(response.status).strip().casefold() == "empty":
            return None
        if response.domain_commit_id is None:
            return None
        return {
            "commit_id": response.domain_commit_id,
            "graph_hash_post": response.graph_hash_post,
            "object_instance_graph_id": response.object_instance_graph_id,
            "root_object_id": response.root_object_id,
            "v": response.head_version,
        }

    async def object_instance_graph_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> object | None:
        response = await self.sdk.get_object_instance_graph_commit(
            actor_id=self.actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            domain_commit_id=commit_id,
        )
        if str(response.status).strip().casefold() == "missing":
            return None
        if response.commit is None:
            return None
        return object_instance_graph_commit_from_payload(response.commit)


@dataclass(frozen=True, slots=True)
class MetaSdkServiceGraphGateway:
    """ServiceGraphGateway-shaped invoke route backed by the Meta SDK."""

    sdk: MetaSdkClient
    graph_context_sdk_factory: GraphContextSdkFactory | None = None

    async def invoke_function(
        self,
        *,
        request: object,
        graph_context: object | None = None,
    ) -> object:
        try:
            sdk = self.sdk
            if graph_context is not None and self.graph_context_sdk_factory is not None:
                sdk = self.graph_context_sdk_factory(graph_context)

            return await sdk.invoke_function(
                actor_id=_required_uuid(request, "actor_id"),
                function_id=_required_uuid(request, "function_id"),
                domain_branch_id=_optional_uuid(
                    getattr(request, "domain_branch_id", None)
                ),
                domain_projection_hash=_optional_string(
                    getattr(request, "domain_projection_hash", None)
                ),
                call_target=_call_target_value(getattr(request, "call_target")),
                target_object_id=_optional_uuid(
                    getattr(request, "target_object_id", None)
                ),
                object_projection_graph_id=_optional_uuid(
                    getattr(request, "object_projection_graph_id", None)
                ),
                args=tuple(getattr(request, "args", ()) or ()),
                kwargs=cast(
                    Mapping[str, object],
                    dict(getattr(request, "kwargs", {}) or {}),
                ),
                expected_graph_hash_pre=_optional_string(
                    getattr(request, "expected_graph_hash_pre", None)
                ),
                expected_head_commit_id=_optional_uuid(
                    getattr(request, "expected_head_commit_id", None)
                ),
                commit=bool(getattr(request, "commit", True)),
                publish=bool(getattr(request, "publish", False)),
            )
        except MetaSdkError as exc:
            return _failed_meta_invoke_function_response(
                request=request,
                error=str(exc),
            )

    async def invoke_temporal_function(
        self,
        *,
        actor_id: UUID,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        before_oig: Mapping[str, object],
        function_id: UUID,
        target_object_id: UUID | None = None,
        object_projection_graph_id: UUID | None = None,
        args: list[object] | None = None,
        kwargs: Mapping[str, object] | None = None,
        expected_graph_hash_pre: str | None = None,
        expected_head_commit_id: UUID | None = None,
        graph_context: object | None = None,
    ) -> object:
        sdk = self.sdk
        if graph_context is not None and self.graph_context_sdk_factory is not None:
            sdk = self.graph_context_sdk_factory(graph_context)
        return await sdk.invoke_temporal_function(
            actor_id=actor_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            before_oig=before_oig,  # type: ignore[arg-type]
            function_id=function_id,
            target_object_id=target_object_id,
            object_projection_graph_id=object_projection_graph_id,
            args=tuple(args or ()),
            kwargs=cast(Mapping[str, Any], dict(kwargs or {})),
            expected_graph_hash_pre=expected_graph_hash_pre,
            expected_head_commit_id=expected_head_commit_id,
        )


@dataclass(frozen=True, slots=True)
class LocalMetaAwarePackageManifestSdkSession:
    """Meta SDK session backed by one local package-manifest runtime."""

    sdk: MetaSdkClient
    api_client: Any
    service_session: Any

    @property
    def operation_context(self) -> Any:
        return self.service_session.operation_context

    @property
    def materialization(self) -> Any:
        return self.service_session.materialization

    def bind(
        self,
        *,
        projection: str,
        actor_id: UUID | None = None,
        branch_id: UUID | None = None,
    ) -> "LocalMetaSdkBoundLane":
        operation_context = self.operation_context
        return LocalMetaSdkBoundLane(
            backend=LocalMetaSdkLaneBackend(
                sdk=self.sdk,
                service_session=self.service_session,
            ),
            binding=LocalMetaSdkLaneBinding(
                actor_id=actor_id or operation_context.actor_id,
                branch_id=branch_id or operation_context.branch_id,
                projection_hash=_resolve_projection_hash(
                    service_session=self.service_session,
                    projection=projection,
                ),
            ),
        )

    def projection_hash(self, projection_name: str) -> str:
        return str(self.service_session.projection_hash(projection_name))

    def object_projection_graph_id(self, projection_name: str) -> UUID:
        return self.service_session.object_projection_graph_id(projection_name)

    def function_id(
        self,
        *,
        class_name: str,
        function_name: str,
        is_constructor: bool | None = None,
    ) -> UUID:
        return self.service_session.function_id(
            class_name=class_name,
            function_name=function_name,
            is_constructor=is_constructor,
        )


@dataclass(frozen=True, slots=True)
class LocalMetaSdkLaneBinding:
    actor_id: UUID
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class LocalMetaSdkLaneInvokeRecord:
    call_target: str
    class_fqn: str
    function_name: str
    function_id: UUID
    object_id: UUID | None
    commit: bool
    publish: bool
    response: Any


@dataclass(frozen=True, slots=True)
class LocalMetaSdkLaneBackend:
    sdk: MetaSdkClient
    service_session: Any

    async def invoke_constructor(
        self,
        *,
        lane: LocalMetaSdkLaneBinding,
        orm_class: type[Any],
        function_name: str,
        payload: Mapping[str, object],
        commit: bool,
        publish: bool,
    ) -> tuple[UUID, Any]:
        _bind_registered_package_orm_classes(service_session=self.service_session)
        class_config = _ensure_orm_class_config_bound(
            service_session=self.service_session,
            orm_class=orm_class,
        )
        function_link = _resolve_function_link(
            class_config=class_config,
            function_name=function_name,
            is_constructor=True,
        )
        projection_hash = _resolve_constructor_projection_hash(
            service_session=self.service_session,
            active_projection_hash=lane.projection_hash,
            class_config=class_config,
            function_link=function_link,
            orm_class=orm_class,
            function_name=function_name,
        )
        opg = _opg_for_projection_hash(
            service_session=self.service_session,
            projection_hash=projection_hash,
        )
        function_id = UUID(
            str(getattr(getattr(function_link, "function_config"), "id"))
        )
        response = await self.sdk.invoke_function(
            actor_id=lane.actor_id,
            function_id=function_id,
            domain_branch_id=lane.branch_id,
            domain_projection_hash=projection_hash,
            call_target="opg_constructor",
            object_projection_graph_id=UUID(str(getattr(opg, "id"))),
            kwargs=_jsonify_payload_mapping(payload),
            commit=commit,
            publish=publish,
        )
        return function_id, response

    async def invoke_instance(
        self,
        *,
        lane: LocalMetaSdkLaneBinding,
        orm_model: Any,
        function_name: str,
        payload: Mapping[str, object],
        commit: bool,
        publish: bool,
    ) -> tuple[UUID, Any]:
        _bind_registered_package_orm_classes(service_session=self.service_session)
        object_id = getattr(orm_model, "id", None)
        if not isinstance(object_id, UUID):
            raise ValueError(
                "Local Meta SDK instance invocation requires an ORM model with "
                f"UUID id: class={type(orm_model).__module__}.{type(orm_model).__name__} "
                f"function={function_name!r}"
            )
        orm_class = type(orm_model)
        class_config = _ensure_orm_class_config_bound(
            service_session=self.service_session,
            orm_class=orm_class,
        )
        function_link = _resolve_function_link(
            class_config=class_config,
            function_name=function_name,
            is_constructor=False,
        )
        function_id = UUID(
            str(getattr(getattr(function_link, "function_config"), "id"))
        )
        projection_hash = _resolve_instance_projection_hash(
            service_session=self.service_session,
            active_projection_hash=lane.projection_hash,
            class_config=class_config,
            orm_class=orm_class,
        )
        response = await self.sdk.invoke_function(
            actor_id=lane.actor_id,
            function_id=function_id,
            domain_branch_id=lane.branch_id,
            domain_projection_hash=projection_hash,
            call_target="instance",
            target_object_id=object_id,
            kwargs=_jsonify_payload_mapping(payload),
            commit=commit,
            publish=publish,
        )
        return function_id, response


@dataclass(slots=True)
class LocalMetaSdkBoundLane:
    backend: LocalMetaSdkLaneBackend
    binding: LocalMetaSdkLaneBinding
    _records: list[LocalMetaSdkLaneInvokeRecord] = field(
        default_factory=list,
        init=False,
        repr=False,
    )
    _last_response: Any | None = field(default=None, init=False, repr=False)
    _last_commit_id: UUID | None = field(default=None, init=False, repr=False)
    _last_head_commit_id: UUID | None = field(default=None, init=False, repr=False)

    @property
    def branch_id(self) -> UUID:
        return self.binding.branch_id

    @property
    def projection_hash(self) -> str:
        return self.binding.projection_hash

    @property
    def records(self) -> tuple[LocalMetaSdkLaneInvokeRecord, ...]:
        return tuple(self._records)

    @property
    def last_response(self) -> Any | None:
        return self._last_response

    @property
    def last_commit_id(self) -> UUID | None:
        return self._last_commit_id

    @property
    def last_head_commit_id(self) -> UUID | None:
        return self._last_head_commit_id

    @contextmanager
    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> Iterator["LocalMetaSdkBoundLane"]:
        from aware_orm.runtime.invocation import (  # noqa: WPS433
            reset_invocation_provider,
            set_invocation_provider,
        )

        provider = _LocalMetaSdkLaneInvocationProvider(
            lane=self,
            commit=bool(commit),
            publish=bool(publish),
        )
        token = set_invocation_provider(provider)
        try:
            yield self
        finally:
            reset_invocation_provider(token)

    async def invoke_constructor(
        self,
        *,
        orm_class: type[Any],
        function_name: str,
        payload: Mapping[str, object],
        commit: bool = True,
        publish: bool = False,
    ) -> Any:
        function_id, response = await self.backend.invoke_constructor(
            lane=self.binding,
            orm_class=orm_class,
            function_name=function_name,
            payload=payload,
            commit=commit,
            publish=publish,
        )
        self._record(
            call_target="opg_constructor",
            class_fqn=f"{orm_class.__module__}.{orm_class.__name__}",
            function_name=function_name,
            function_id=function_id,
            object_id=None,
            commit=commit,
            publish=publish,
            response=response,
        )
        self._assert_succeeded(
            response=response,
            label=f"{orm_class.__module__}.{orm_class.__name__}.{function_name}",
        )
        return response

    async def invoke_instance(
        self,
        *,
        orm_model: Any,
        function_name: str,
        payload: Mapping[str, object],
        commit: bool = True,
        publish: bool = False,
    ) -> Any:
        function_id, response = await self.backend.invoke_instance(
            lane=self.binding,
            orm_model=orm_model,
            function_name=function_name,
            payload=payload,
            commit=commit,
            publish=publish,
        )
        object_id = getattr(orm_model, "id", None)
        self._record(
            call_target="instance",
            class_fqn=f"{type(orm_model).__module__}.{type(orm_model).__name__}",
            function_name=function_name,
            function_id=function_id,
            object_id=object_id if isinstance(object_id, UUID) else None,
            commit=commit,
            publish=publish,
            response=response,
        )
        self._assert_succeeded(
            response=response,
            label=f"{type(orm_model).__module__}.{type(orm_model).__name__}.{function_name}",
        )
        return response

    async def get_head(self) -> Any:
        return await self.backend.sdk.get_lane_head(
            actor_id=self.binding.actor_id,
            domain_branch_id=self.binding.branch_id,
            domain_projection_hash=self.binding.projection_hash,
        )

    async def get_last_commit(self) -> Any:
        if self._last_commit_id is None:
            raise RuntimeError("Local Meta SDK lane has no committed invocation.")
        return await self.backend.sdk.get_object_instance_graph_commit(
            actor_id=self.binding.actor_id,
            domain_branch_id=self.binding.branch_id,
            domain_projection_hash=self.binding.projection_hash,
            domain_commit_id=self._last_commit_id,
        )

    def assert_last_response(
        self,
        expectation: OigCommitExpectation | None = None,
    ) -> Any:
        if self._last_response is None:
            raise AssertionError("Local Meta SDK lane has no invocation response.")
        assert_oig_commit_matches(self._last_response, expectation)
        return self._last_response

    async def assert_last_commit(
        self,
        expectation: OigCommitExpectation | None = None,
    ) -> Any:
        commit = await self.get_last_commit()
        assert_oig_commit_matches(commit, expectation)
        return commit

    def _record(
        self,
        *,
        call_target: str,
        class_fqn: str,
        function_name: str,
        function_id: UUID,
        object_id: UUID | None,
        commit: bool,
        publish: bool,
        response: Any,
    ) -> None:
        response_branch_id = getattr(response, "domain_branch_id", None)
        if isinstance(response_branch_id, UUID):
            self.binding = LocalMetaSdkLaneBinding(
                actor_id=self.binding.actor_id,
                branch_id=response_branch_id,
                projection_hash=self.binding.projection_hash,
            )
        commit_id = getattr(response, "domain_commit_id", None)
        if isinstance(commit_id, UUID):
            self._last_commit_id = commit_id
        object_instance_graph_commit_id = getattr(
            response,
            "object_instance_graph_commit_id",
            None,
        )
        if isinstance(object_instance_graph_commit_id, UUID):
            self._last_head_commit_id = object_instance_graph_commit_id
        self._last_response = response
        self._records.append(
            LocalMetaSdkLaneInvokeRecord(
                call_target=call_target,
                class_fqn=class_fqn,
                function_name=function_name,
                function_id=function_id,
                object_id=object_id,
                commit=commit,
                publish=publish,
                response=response,
            )
        )

    @staticmethod
    def _assert_succeeded(*, response: Any, label: str) -> None:
        if getattr(response, "status", None) == "succeeded":
            return
        error = getattr(response, "error", None)
        if error:
            raise RuntimeError(f"{label} failed: {error}")
        raise RuntimeError(f"{label} failed")


@dataclass(frozen=True, slots=True)
class _LocalMetaSdkLaneInvocationProvider:
    lane: LocalMetaSdkBoundLane
    commit: bool
    publish: bool

    async def invoke_instance(
        self,
        *,
        orm_model: Any,
        function_name: str,
        payload: Mapping[str, object],
    ) -> object:
        response = await self.lane.invoke_instance(
            orm_model=orm_model,
            function_name=function_name,
            payload={str(key): value for key, value in dict(payload).items()},
            commit=self.commit,
            publish=self.publish,
        )
        return cast(object, response.payload)

    async def invoke_constructor(
        self,
        *,
        orm_class: type[Any],
        function_name: str,
        payload: Mapping[str, object],
    ) -> object:
        response = await self.lane.invoke_constructor(
            orm_class=orm_class,
            function_name=function_name,
            payload={str(key): value for key, value in dict(payload).items()},
            commit=self.commit,
            publish=self.publish,
        )
        return cast(object, response.payload)


def build_local_meta_sdk_session_for_aware_package_manifests(
    *,
    package_manifest_paths: Iterable[Path],
    workspace_root: Path | None = None,
    aware_root: Path | None = None,
    composite_name: str = "Aware Local Meta SDK Package Session",
    projection_name: str | None = None,
    actor_id: UUID | None = None,
    branch_id: UUID | None = None,
    endpoint: str = "aware-meta-service://local",
    request_timeout_s: float = 10.0,
    service_name: str = "aware_meta",
    invocation_context: Mapping[str, object] | None = None,
    event_bus: object | None = None,
    event_store: object | None = None,
    commit_store: object | None = None,
    generated_language_handler_module: object | None = None,
    generated_language_handler_modules: Sequence[object] = (),
    generated_language_handler_resolver: object | None = None,
    strict_package_graph_cache: bool = False,
    source_analysis_allowed_manifest_paths: Iterable[Path] = (),
) -> LocalMetaAwarePackageManifestSdkSession:
    """Build a Meta SDK session backed by local package manifests."""

    service_session = build_local_meta_service_api_session_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=workspace_root,
        aware_root=aware_root,
        composite_name=composite_name,
        projection_name=projection_name,
        actor_id=actor_id,
        branch_id=branch_id,
        endpoint=endpoint,
        request_timeout_s=request_timeout_s,
        service_name=service_name,
        invocation_context=invocation_context,
        event_bus=event_bus,
        event_store=event_store,
        commit_store=commit_store,
        generated_language_handler_module=generated_language_handler_module,
        generated_language_handler_modules=generated_language_handler_modules,
        generated_language_handler_resolver=generated_language_handler_resolver,
        strict_package_graph_cache=strict_package_graph_cache,
        source_analysis_allowed_manifest_paths=source_analysis_allowed_manifest_paths,
    )
    _bind_registered_package_orm_classes(service_session=service_session)
    sdk = MetaSdkClient(api_client=service_session.api_client)
    return LocalMetaAwarePackageManifestSdkSession(
        sdk=sdk,
        api_client=service_session.api_client,
        service_session=service_session,
    )


def build_local_meta_sdk_client(**kwargs: Any) -> MetaSdkClient:
    """Build a Meta SDK client backed by the local Meta service boundary."""

    return MetaSdkClient(api_client=build_local_meta_service_api_client(**kwargs))


def build_local_meta_sdk_client_for_aware_package_manifests(
    **kwargs: Any,
) -> MetaSdkClient:
    """Build a local Meta SDK client from package manifests."""

    return MetaSdkClient(
        api_client=build_local_meta_service_api_client_for_aware_package_manifests(
            **kwargs
        )
    )


def build_local_meta_sdk_lane_store(
    *,
    actor_id: UUID | None = None,
    endpoint: str = "aware-meta-service://local",
    request_timeout_s: float = 10.0,
    service_name: str = "aware_meta",
    invocation_context: Mapping[str, object] | None = None,
    event_bus: object | None = None,
    event_store: object | None = None,
    commit_store: object | None = None,
) -> MetaSdkLaneStore:
    """Build a local Meta SDK lane store for commit-head reads."""

    return MetaSdkLaneStore(
        sdk=build_local_meta_sdk_client(
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            service_name=service_name,
            invocation_context=invocation_context,
            event_bus=event_bus,
            event_store=event_store,
            commit_store=commit_store,
        ),
        actor_id=actor_id,
    )


def build_local_meta_sdk_service_graph_gateway(
    *,
    graph_context: object | None = None,
    graph_context_provider: object | None = None,
    endpoint: str = "aware-meta-service://local",
    request_timeout_s: float = 10.0,
    service_name: str = "aware_meta",
    invocation_context: Mapping[str, object] | None = None,
    event_bus: object | None = None,
    event_store: object | None = None,
    commit_store: object | None = None,
    generated_language_handler_resolver: object | None = None,
    generated_language_handler_module: object | None = None,
) -> MetaSdkServiceGraphGateway:
    """Build a local service graph gateway through the Meta service boundary."""

    if graph_context is not None and graph_context_provider is not None:
        raise ValueError("Pass graph_context or graph_context_provider, not both.")

    from .api_service_protocol import (  # noqa: WPS433
        build_aware_meta_service_protocol_handler,
    )

    shared_handler = build_aware_meta_service_protocol_handler(
        event_bus=event_bus,  # type: ignore[arg-type]
        event_store=event_store,  # type: ignore[arg-type]
        commit_store=commit_store,  # type: ignore[arg-type]
        generated_language_handler_resolver=generated_language_handler_resolver,
        generated_language_handler_module=generated_language_handler_module,
    )

    def _api_client_for_provider(provider: object | None) -> object:
        return build_local_meta_service_api_client(
            handler=shared_handler,
            graph_context_provider=provider,
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            service_name=service_name,
            invocation_context=invocation_context,
        )

    resolved_provider = graph_context_provider
    if resolved_provider is None and graph_context is not None:
        resolved_provider = _StaticGraphContextProvider(graph_context=graph_context)

    def _sdk_for_graph_context(call_graph_context: object) -> MetaSdkClient:
        return MetaSdkClient(
            api_client=_api_client_for_provider(
                _StaticGraphContextProvider(graph_context=call_graph_context)
            )
        )

    return MetaSdkServiceGraphGateway(
        sdk=MetaSdkClient(api_client=_api_client_for_provider(resolved_provider)),
        graph_context_sdk_factory=_sdk_for_graph_context,
    )


def build_local_meta_lane_store(
    *,
    root_dir: Path | None = None,
    commit_store: object | None = None,
    snapshot_store: object | None = None,
    materializer: object | None = None,
) -> LocalMetaLaneStore:
    """Build a local Meta lane facade from service-owned stores."""

    resolved_commits = commit_store
    if resolved_commits is None:
        resolved_commits = build_local_meta_commit_store(root_dir=root_dir)
    resolved_snapshots = snapshot_store
    if resolved_snapshots is None:
        resolved_snapshots = build_local_meta_snapshot_store(root_dir=root_dir)
    resolved_materializer = materializer
    if resolved_materializer is None:
        resolved_materializer = build_local_meta_oig_materializer(
            commits=resolved_commits,
            snapshots=resolved_snapshots,
        )
    return LocalMetaLaneStore(
        _commits=resolved_commits,
        _snapshots=resolved_snapshots,
        _materializer=resolved_materializer,
    )


def start_local_meta_lane_head_receipt_relay() -> LocalMetaLaneHeadReceiptRelay:
    """Start the local Meta lane-head relay at the service boundary."""

    from aware_meta.receipts.lane_head_receipt_relay import (  # noqa: WPS433
        LaneHeadReceiptRelay,
    )

    relay = LaneHeadReceiptRelay()
    relay.start()
    return LocalMetaLaneHeadReceiptRelay(_relay=relay)


def get_local_meta_lane_commit_receipt_bus() -> object:
    from aware_meta.receipts.lane_commit_receipt_bus import (  # noqa: WPS433
        LaneCommitReceiptBus,
    )

    return LaneCommitReceiptBus.instance()


def dispatch_local_meta_lane_commit_receipt(notification: object) -> None:
    from aware_meta.receipts.notifications import (  # noqa: WPS433
        LaneCommitReceiptNotification,
    )

    if isinstance(notification, LaneCommitReceiptNotification):
        meta_notification = notification
    else:
        model_dump = getattr(notification, "model_dump", None)
        payload = (
            model_dump(mode="python", exclude_none=True)
            if callable(model_dump)
            else notification
        )
        meta_notification = LaneCommitReceiptNotification.model_validate(payload)
    get_local_meta_lane_commit_receipt_bus().dispatch(meta_notification)


def get_local_meta_lane_event_receipt_bus() -> object:
    from aware_meta.receipts.lane_event_receipt_bus import (  # noqa: WPS433
        LaneEventReceiptBus,
    )

    return LaneEventReceiptBus.instance()


def get_local_meta_lane_action_execution_receipt_bus() -> object:
    from aware_meta.receipts.lane_action_execution_receipt_bus import (  # noqa: WPS433
        LaneActionExecutionReceiptBus,
    )

    return LaneActionExecutionReceiptBus.instance()


def get_local_meta_lane_action_feedback_receipt_bus() -> object:
    from aware_meta.receipts.lane_action_feedback_receipt_bus import (  # noqa: WPS433
        LaneActionFeedbackReceiptBus,
    )

    return LaneActionFeedbackReceiptBus.instance()


def get_local_meta_lane_action_terminal_receipt_bus() -> object:
    from aware_meta.receipts.lane_action_terminal_receipt_bus import (  # noqa: WPS433
        LaneActionTerminalReceiptBus,
    )

    return LaneActionTerminalReceiptBus.instance()


def _ensure_orm_class_config_bound(
    *,
    service_session: Any,
    orm_class: type[Any],
) -> Any:
    class_config = service_session.resolver.class_config(orm_class.__name__)
    bind_class_config = getattr(orm_class, "bind_class_config", None)
    if not callable(bind_class_config):
        raise RuntimeError(
            "Local Meta SDK ORM lane requires generated ORM model classes with "
            f"bind_class_config: class={orm_class.__module__}.{orm_class.__name__}"
        )
    from aware_orm.registry import ORMModelRegistry  # noqa: WPS433

    _ = ORMModelRegistry.register_class_stub(orm_class)
    bind_class_config(class_config)
    class_fqn = f"{orm_class.__module__}.{orm_class.__name__}"
    _ = ORMModelRegistry.attach_class_config(class_fqn, class_config)
    return class_config


def _bind_registered_package_orm_classes(*, service_session: Any) -> None:
    graph_catalog = getattr(
        getattr(service_session, "resolver", None), "graph_catalog", None
    )
    if graph_catalog is None:
        return
    class_configs = getattr(graph_catalog, "class_configs_by_id", {}) or {}
    if not class_configs:
        return

    from aware_orm.registry import ORMModelRegistry  # noqa: WPS433

    for class_config in class_configs.values():
        class_name = str(getattr(class_config, "name", "") or "").strip()
        if not class_name:
            continue
        orm_class = ORMModelRegistry.get_class_by_name(class_name)
        if orm_class is None:
            continue
        bind_class_config = getattr(orm_class, "bind_class_config", None)
        if not callable(bind_class_config):
            continue
        bind_class_config(class_config)
        class_fqn = f"{orm_class.__module__}.{orm_class.__name__}"
        _ = ORMModelRegistry.attach_class_config(class_fqn, class_config)


def _resolve_projection_hash(
    *,
    service_session: Any,
    projection: str,
) -> str:
    token = str(projection or "").strip()
    if not token:
        raise ValueError("projection is required")
    resolver = getattr(service_session, "resolver", None)
    lookup = getattr(resolver, "object_projection_graph_for_projection_hash", None)
    if callable(lookup):
        try:
            lookup(token)
            return token
        except Exception as exc:
            if _looks_like_projection_hash(token):
                raise ValueError(f"projection hash is not available: {token}") from exc
    if _looks_like_projection_hash(token):
        return token
    return str(service_session.projection_hash(token))


def _resolve_function_link(
    *,
    class_config: Any,
    function_name: str,
    is_constructor: bool | None,
) -> Any:
    matches = []
    for edge in getattr(class_config, "class_config_function_configs", ()) or ():
        function_config = getattr(edge, "function_config", None)
        if function_config is None:
            continue
        if getattr(function_config, "name", None) != function_name:
            continue
        if (
            is_constructor is not None
            and bool(getattr(edge, "is_constructor", False)) is not is_constructor
        ):
            continue
        matches.append(edge)
    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one FunctionConfig for local Meta SDK ORM lane: "
            f"class={getattr(class_config, 'name', None)!r} "
            f"function={function_name!r} is_constructor={is_constructor!r} "
            f"matches={len(matches)}"
        )
    return matches[0]


def _resolve_constructor_projection_hash(
    *,
    service_session: Any,
    active_projection_hash: str,
    class_config: Any,
    function_link: Any,
    orm_class: type[Any],
    function_name: str,
) -> str:
    candidates = tuple(
        opg
        for opg in _lookup_opgs_for_class(
            service_session=service_session,
            class_config_id=UUID(str(getattr(class_config, "id"))),
        )
        if any(
            getattr(constructor, "function_constructor_id", None)
            == getattr(function_link, "id", None)
            for constructor in getattr(
                opg,
                "object_projection_graph_constructors",
                (),
            )
            or ()
        )
    )
    if not candidates:
        raise RuntimeError(
            "No ObjectProjectionGraph constructor owns the local Meta SDK ORM "
            f"call: class={orm_class.__module__}.{orm_class.__name__} "
            f"function={function_name!r} class_config_id={getattr(class_config, 'id', None)}"
        )
    if len(candidates) == 1:
        return str(getattr(candidates[0], "projection_hash"))
    candidate_hashes = sorted(
        str(getattr(opg, "projection_hash")) for opg in candidates
    )
    raise RuntimeError(
        "Ambiguous ObjectProjectionGraph constructor ownership for local Meta "
        f"SDK ORM call: class={orm_class.__module__}.{orm_class.__name__} "
        f"function={function_name!r} active_projection_hash={active_projection_hash!r} "
        f"candidate_projection_hashes={candidate_hashes}"
    )


def _resolve_instance_projection_hash(
    *,
    service_session: Any,
    active_projection_hash: str,
    class_config: Any,
    orm_class: type[Any],
) -> str:
    candidates = _lookup_opgs_for_class(
        service_session=service_session,
        class_config_id=UUID(str(getattr(class_config, "id"))),
    )
    if not candidates:
        raise RuntimeError(
            "No ObjectProjectionGraph membership found for local Meta SDK ORM "
            f"instance call: class={orm_class.__module__}.{orm_class.__name__} "
            f"class_config_id={getattr(class_config, 'id', None)}"
        )
    candidate_hashes = sorted(
        str(getattr(opg, "projection_hash")) for opg in candidates
    )
    if active_projection_hash in candidate_hashes:
        return active_projection_hash
    if len(candidate_hashes) == 1:
        return candidate_hashes[0]
    raise RuntimeError(
        "Ambiguous ObjectProjectionGraph membership for local Meta SDK ORM "
        f"instance call: class={orm_class.__module__}.{orm_class.__name__} "
        f"active_projection_hash={active_projection_hash!r} "
        f"candidate_projection_hashes={candidate_hashes}"
    )


def _lookup_opgs_for_class(
    *,
    service_session: Any,
    class_config_id: UUID,
) -> tuple[Any, ...]:
    resolver = getattr(service_session, "resolver", None)
    lookup = getattr(resolver, "object_projection_graphs_for_class_config_id", None)
    if not callable(lookup):
        raise RuntimeError(
            "Local Meta SDK package session requires resolver."
            "object_projection_graphs_for_class_config_id()."
        )
    return tuple(lookup(class_config_id))


def _opg_for_projection_hash(
    *,
    service_session: Any,
    projection_hash: str,
) -> Any:
    resolver = getattr(service_session, "resolver", None)
    lookup = getattr(resolver, "object_projection_graph_for_projection_hash", None)
    if not callable(lookup):
        raise RuntimeError(
            "Local Meta SDK package session requires resolver."
            "object_projection_graph_for_projection_hash()."
        )
    return lookup(projection_hash)


def _looks_like_projection_hash(value: str) -> bool:
    return value.startswith(("sha256:", "projection:"))


def _jsonify_payload_mapping(payload: Mapping[str, object]) -> dict[str, Any]:
    return {str(key): _jsonify_payload(value) for key, value in dict(payload).items()}


def _jsonify_payload(payload: object) -> Any:
    if payload is None or isinstance(payload, (str, int, float, bool)):
        return payload
    if isinstance(payload, Enum):
        return _jsonify_payload(payload.value)
    if isinstance(payload, UUID):
        return str(payload)
    if isinstance(payload, Path):
        return str(payload)
    if isinstance(payload, (list, tuple, set)):
        return [_jsonify_payload(value) for value in payload]
    if isinstance(payload, Mapping):
        return {str(key): _jsonify_payload(value) for key, value in payload.items()}
    model_dump = getattr(payload, "model_dump", None)
    if callable(model_dump):
        return _jsonify_payload(model_dump(mode="json", exclude_none=True))
    return str(payload)


def _local_lane_head_from_mapping(
    *,
    branch_id: UUID,
    projection_hash: str,
    payload: Mapping[str, object],
) -> LocalMetaLaneHead | None:
    commit_id = _optional_uuid(payload.get("commit_id"))
    if commit_id is None:
        return None
    return LocalMetaLaneHead(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        graph_hash_post=_optional_string(payload.get("graph_hash_post")),
        object_instance_graph_id=_optional_uuid(
            payload.get("object_instance_graph_id")
        ),
        root_object_id=_optional_uuid(payload.get("root_object_id")),
        version=_optional_int(payload.get("v")),
    )


async def _await_maybe(value: object | Awaitable[object]) -> object:
    if inspect.isawaitable(value):
        return await value
    return value


def _failed_meta_invoke_function_response(
    *,
    request: object,
    error: str,
) -> MetaGraphInvokeFunctionResponse:
    return MetaGraphInvokeFunctionResponse(
        actor_id=_optional_uuid(getattr(request, "actor_id", None)),
        domain_branch_id=_optional_uuid(getattr(request, "domain_branch_id", None)),
        domain_projection_hash=_optional_string(
            getattr(request, "domain_projection_hash", None)
        ),
        status="failed",
        error=error,
    )


def _call_target_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    normalized = str(raw_value or "").strip()
    if normalized not in {"instance", "opg_constructor"}:
        raise MetaSdkError(f"Unsupported service graph call target: {value!r}")
    return normalized


def _required_uuid(value: object, field_name: str) -> UUID:
    resolved = _optional_uuid(getattr(value, field_name, value))
    if resolved is None:
        raise MetaSdkError(f"Service graph invocation requires {field_name}.")
    return resolved


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    return None


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, slots=True)
class _StaticGraphContextProvider:
    graph_context: object

    async def resolve_graph_context(self) -> object:
        return self.graph_context


__all__ = [
    "build_local_meta_commit_store",
    "build_local_meta_lane_store",
    "build_local_meta_oig_materializer",
    "build_local_meta_sdk_client",
    "build_local_meta_sdk_client_for_aware_package_manifests",
    "build_local_meta_sdk_lane_store",
    "build_local_meta_sdk_service_graph_gateway",
    "build_local_meta_service_api_client",
    "build_local_meta_service_api_client_for_aware_package_manifests",
    "build_local_meta_service_api_session",
    "build_local_meta_service_api_session_for_aware_package_manifests",
    "build_local_meta_snapshot_store",
    "build_local_meta_runtime_index_snapshot",
    "build_meta_graph_runtime_index_snapshot",
    "dispatch_local_meta_lane_commit_receipt",
    "ensure_projection_readiness",
    "get_local_meta_lane_action_execution_receipt_bus",
    "get_local_meta_lane_action_feedback_receipt_bus",
    "get_local_meta_lane_action_terminal_receipt_bus",
    "get_local_meta_lane_commit_receipt_bus",
    "get_local_meta_lane_event_receipt_bus",
    "LaneHeadReceiptRelay",
    "load_local_meta_graph_context",
    "LocalGraphCommitReceipt",
    "LocalGraphInvokeFunctionInput",
    "LocalGraphRuntime",
    "LocalGraphRuntimeContext",
    "LocalGraphRuntimeIndexSnapshot",
    "LocalMetaAwarePackageManifestSdkSession",
    "LocalMetaLaneHead",
    "LocalMetaLaneHeadReceiptRelay",
    "LocalMetaLaneStore",
    "LocalMetaSdkBoundLane",
    "LocalMetaSdkLaneBinding",
    "LocalMetaSdkLaneInvokeRecord",
    "MaterializationExecutionError",
    "MaterializationLaneContext",
    "materialize_local_meta_lane_oig",
    "MetaSdkLaneStore",
    "MetaSdkServiceGraphGateway",
    "ProjectionReadinessModes",
    "ProjectionReadinessRequirement",
    "ProjectionReadinessResult",
    "read_local_meta_api_activation_read_model",
    "read_local_meta_runtime_read_model",
    "build_local_meta_sdk_session_for_aware_package_manifests",
    "start_local_meta_lane_head_receipt_relay",
]
