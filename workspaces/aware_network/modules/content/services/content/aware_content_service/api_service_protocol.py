from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, cast
from pathlib import PurePosixPath
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_content.builder import get_text
from aware_content_ontology.content.content import Content
from aware_content_ontology.content.content_enums import ContentSource
from aware_content_ontology.package.content_package_enums import (
    ContentPackageArtifactStatus,
)
from aware_content_ontology.part.content_part_content import ContentPartContent
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.stable_ids import stable_content_id
from aware_content_ontology.stable_ids import stable_content_package_id
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest as InvokeFunctionRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionResponse as InvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_content_service_dto.content.content_service_operation import (
    CommitContentTextRequest,
    CommitContentTextResponse,
    ContentOperationReceipt,
    ContentPackageArtifactProjectionV1,
    ContentPackageExportDocumentV1,
    ContentPackageMaterializationResultV1,
    ContentPackageMaterializedArtifactRefV1,
    ContentTextPartV1,
    ContentTextCommitResultV1,
    ContentTextResolutionV1,
    MaterializeContentPackageRequest,
    MaterializeContentPackageResponse,
    ResolveContentTextRequest,
    ResolveContentTextResponse,
)
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    current_service_api_host_context,
)
from aware_service_runtime.contracts import ServiceGraphGateway, ServiceOperationContext
from aware_types import JsonArray, JsonObject

ContentIdentityResolver = Callable[
    [UUID, UUID | None],
    UUID | None | Awaitable[UUID | None],
]
ContentPackageMaterializer = Callable[
    [ContentPackageExportDocumentV1],
    ContentPackageMaterializationResultV1
    | Awaitable[ContentPackageMaterializationResultV1],
]


@dataclass(frozen=True, slots=True)
class _ContentCommitEvidence:
    domain_commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    service_host_receipt_ref: str | None = None
    metadata: JsonObject = field(default_factory=JsonObject)

    @property
    def has_any(self) -> bool:
        return (
            self.domain_commit_id is not None
            or self.object_instance_graph_commit_id is not None
            or self.service_host_receipt_ref is not None
        )


@dataclass(frozen=True, slots=True)
class _ContentRuntimeContext:
    graph_gateway: ServiceGraphGateway
    runtime_index: MetaGraphRuntimeIndex
    content_opg_id: UUID
    content_projection_hash: str
    content_package_opg_id: UUID
    content_package_projection_hash: str
    function_ids: dict[str, UUID]


@dataclass(frozen=True, slots=True)
class _EnvironmentInvocationContext:
    actor_id: UUID | None
    environment_id: UUID
    process_id: UUID | None
    thread_id: UUID | None


def build_aware_content_service_protocol_handler(
    *,
    content_identity_resolver: ContentIdentityResolver | None = None,
    content_package_materializer: ContentPackageMaterializer | None = None,
    blob_store: object | None = None,
) -> object:
    return _AwareContentServiceProtocolHandler(
        support=_ContentProtocolSupport(
            content_identity_resolver=content_identity_resolver,
            content_package_materializer=content_package_materializer,
            blob_store=blob_store,
        )
    )


@dataclass(frozen=True, slots=True)
class _ContentProtocolSupport:
    content_identity_resolver: ContentIdentityResolver | None = None
    content_package_materializer: ContentPackageMaterializer | None = None
    blob_store: object | None = None

    async def resolve_content_id(self, request: ResolveContentTextRequest) -> UUID:
        if request.content_id is not None:
            return request.content_id
        identity_id = request.content_class_instance_identity_id
        if identity_id is None:
            raise ValueError(
                "resolve_content_text requires content_id or "
                "content_class_instance_identity_id."
            )
        resolver = self.content_identity_resolver
        if resolver is None:
            raise ValueError(
                "content_class_instance_identity_id resolution requires a "
                "Content service host resolver."
            )
        resolved = resolver(identity_id, request.content_class_config_id)
        if inspect.isawaitable(resolved):
            resolved = await resolved
        if resolved is None:
            raise ValueError(
                "Content service could not resolve content_class_instance_identity_id "
                f"{identity_id}."
            )
        return resolved

    def receipt(
        self,
        *,
        operation: str,
        status: str,
        content_id: UUID | None = None,
        content_package_id: UUID | None = None,
        domain_commit_id: UUID | None = None,
        object_instance_graph_commit_id: UUID | None = None,
        service_host_receipt_ref: str | None = None,
        package_name: str | None = None,
        digest: str | None = None,
        size_bytes: int | None = None,
        extra: dict[str, object] | None = None,
    ) -> ContentOperationReceipt:
        return ContentOperationReceipt(
            operation=operation,
            status=status,
            content_id=content_id,
            content_package_id=content_package_id,
            domain_commit_id=domain_commit_id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
            service_host_receipt_ref=service_host_receipt_ref,
            package_name=package_name,
            digest=digest,
            size_bytes=size_bytes,
            metadata=cast(JsonObject, dict(extra or {})),
        )

    async def materialize_content_package(
        self,
        package_export: ContentPackageExportDocumentV1,
    ) -> ContentPackageMaterializationResultV1:
        materializer = self.content_package_materializer
        if materializer is None:
            return await _materialize_content_package_export(
                package_export,
                support=self,
            )
        result = materializer(package_export)
        if inspect.isawaitable(result):
            result = await result
        return result

    def host_context(self) -> ServiceApiHostContext:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Content service protocol requires an active Service API host context."
            )
        return host_context

    async def runtime_context(self) -> _ContentRuntimeContext:
        host_context = self.host_context()
        graph_gateway = host_context.graph_gateway
        if graph_gateway is None:
            raise RuntimeError(
                "Content service protocol requires a Service graph gateway."
            )
        runtime_index = self._coerce_runtime_index(
            await self._resolve_graph_context(
                host_context=host_context,
                graph_gateway=graph_gateway,
            )
        )
        return _resolve_content_runtime_context(
            graph_gateway=graph_gateway,
            runtime_index=runtime_index,
        )

    async def _resolve_graph_context(
        self,
        *,
        host_context: ServiceApiHostContext,
        graph_gateway: object,
    ) -> object:
        if host_context.materialization is not None:
            return host_context.materialization.graph_context
        if host_context.graph_context_provider is not None:
            return await host_context.graph_context_provider.resolve_graph_context()
        resolve_graph_context = getattr(graph_gateway, "resolve_graph_context", None)
        if callable(resolve_graph_context):
            resolved = resolve_graph_context()
            if inspect.isawaitable(resolved):
                return await resolved
            return resolved
        raise RuntimeError(
            "Content service protocol requires a Service graph context."
        )

    @staticmethod
    def _coerce_runtime_index(graph_context: object) -> MetaGraphRuntimeIndex:
        return cast(
            MetaGraphRuntimeIndex,
            getattr(graph_context, "index", graph_context),
        )


class _ContentTextCapabilityHandler:
    def __init__(self, *, support: _ContentProtocolSupport) -> None:
        self._support = support

    async def resolve_content_text(
        self,
        request: ResolveContentTextRequest,
    ) -> ResolveContentTextResponse:
        content_id: UUID | None = None
        try:
            content_id = await self._support.resolve_content_id(request)
            content = await Content.by_id(content_id)
            if content is None:
                raise FileNotFoundError(f"Content not found: {content_id}")
            resolution = _resolve_content_text(
                content=content,
                request=request,
                blob_store=self._support.blob_store,
            )
            return ResolveContentTextResponse(
                request_id=request.request_id,
                success=True,
                resolution=resolution,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="succeeded",
                    content_id=resolution.content_id,
                    digest=resolution.digest,
                    size_bytes=resolution.size_bytes,
                    extra={
                        "part_count": len(resolution.parts),
                        "source_kind": resolution.source_kind,
                    },
                ),
            )
        except Exception as exc:
            return ResolveContentTextResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                resolution=None,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="failed",
                    content_id=content_id,
                    extra={"error": str(exc)},
                ),
            )

    async def commit_content_text(
        self,
        request: CommitContentTextRequest,
    ) -> CommitContentTextResponse:
        content_id: UUID | None = None
        try:
            result = await _commit_content_text(request=request, support=self._support)
            content_id = result.content_id
            return CommitContentTextResponse(
                request_id=request.request_id,
                success=True,
                commit_result=result,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="succeeded",
                    content_id=result.content_id,
                    domain_commit_id=result.domain_commit_id,
                    object_instance_graph_commit_id=(
                        result.object_instance_graph_commit_id
                    ),
                    service_host_receipt_ref=result.service_host_receipt_ref,
                    digest=result.digest,
                    size_bytes=result.size_bytes,
                    extra={
                        "content_key": result.content_key,
                        "source_kind": result.source_kind,
                        "source_ref": result.source_ref,
                    },
                ),
            )
        except Exception as exc:
            return CommitContentTextResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                commit_result=None,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="failed",
                    content_id=content_id,
                    digest=request.digest,
                    size_bytes=request.size_bytes,
                    extra={"error": str(exc)},
                ),
            )


class _ContentPackageCapabilityHandler:
    def __init__(self, *, support: _ContentProtocolSupport) -> None:
        self._support = support

    async def materialize_content_package(
        self,
        request: MaterializeContentPackageRequest,
    ) -> MaterializeContentPackageResponse:
        try:
            result = await self._support.materialize_content_package(
                request.package_export
            )
            return MaterializeContentPackageResponse(
                request_id=request.request_id,
                success=True,
                materialization=result,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="succeeded",
                    content_id=result.content_id,
                    content_package_id=result.content_package_id,
                    domain_commit_id=result.domain_commit_id,
                    object_instance_graph_commit_id=(
                        result.object_instance_graph_commit_id
                    ),
                    service_host_receipt_ref=result.service_host_receipt_ref,
                    package_name=result.package_name,
                    digest=result.digest,
                    size_bytes=result.size_bytes,
                    extra={
                        "artifact_ref_count": len(result.artifact_refs),
                        "source_provider_key": result.source_provider_key,
                        "source_ref": result.source_ref,
                        "target_path": result.target_path,
                    },
                ),
            )
        except Exception as exc:
            package_export = request.package_export
            return MaterializeContentPackageResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                materialization=None,
                receipt=self._support.receipt(
                    operation=request.operation,
                    status="failed",
                    package_name=package_export.package_name,
                    digest=package_export.digest,
                    size_bytes=package_export.size_bytes,
                    extra={
                        "error": str(exc),
                        "source_provider_key": package_export.source_provider_key,
                        "source_ref": package_export.source_ref,
                    },
                ),
            )


class _ContentApiServiceProtocolHandler:
    def __init__(self, *, support: _ContentProtocolSupport) -> None:
        self.package = _ContentPackageCapabilityHandler(support=support)
        self.text = _ContentTextCapabilityHandler(support=support)


class _AwareContentServiceProtocolHandler:
    def __init__(self, *, support: _ContentProtocolSupport) -> None:
        self.content = _ContentApiServiceProtocolHandler(support=support)


def _resolve_content_text(
    *,
    content: Content,
    request: ResolveContentTextRequest,
    blob_store: object | None,
) -> ContentTextResolutionV1:
    if content.id is None:
        raise ValueError("Content is missing id.")

    parts: list[ContentTextPartV1] = []
    for edge in sorted(
        content.content_part_contents,
        key=lambda value: int(value.position or 0),
    ):
        part = _resolve_edge_text_part(
            edge=edge,
            media_type=request.media_type,
            blob_store=blob_store,
        )
        parts.append(part)

    text = "".join(part.text for part in parts)
    truncated = False
    if request.max_chars is not None and request.max_chars >= 0:
        truncated = len(text) > request.max_chars
        text = text[: request.max_chars]

    encoded = text.encode("utf-8")
    digest = sha256(encoded).hexdigest()
    visible_parts = parts if request.include_parts else []
    source_kind = _combined_source_kind(parts)
    provenance: dict[str, object] = {
        "part_count": len(parts),
        "truncated": truncated,
    }
    if request.max_chars is not None:
        provenance["max_chars"] = request.max_chars

    return ContentTextResolutionV1(
        content_id=content.id,
        content_key=content.key,
        title=content.title,
        media_type=request.media_type,
        text=text,
        parts=visible_parts,
        digest=digest,
        size_bytes=len(encoded),
        source_kind=source_kind,
        provenance=cast(JsonObject, provenance),
    )


def _resolve_edge_text_part(
    *,
    edge: ContentPartContent,
    media_type: str,
    blob_store: object | None,
) -> ContentTextPartV1:
    content_part = edge.content_part
    content_part_text = content_part.content_part_text
    if content_part_text is None:
        text = ""
        source_kind = "non_text"
        content_part_text_id = None
        part_key = None
    else:
        text = _read_content_part_text(content_part_text, blob_store=blob_store)
        source_kind = _source_kind(content_part_text)
        content_part_text_id = content_part_text.id
        part_key = content_part_text.key
    encoded = text.encode("utf-8")
    digest = sha256(encoded).hexdigest()
    return ContentTextPartV1(
        content_part_content_id=edge.id,
        content_part_id=content_part.id,
        content_part_text_id=content_part_text_id,
        position=int(edge.position or 0),
        part_key=part_key,
        media_type=media_type,
        text=text,
        digest=digest,
        size_bytes=len(encoded),
        source_kind=source_kind,
        provenance=JsonObject({}),
    )


def _read_content_part_text(
    content_part_text: ContentPartText,
    *,
    blob_store: object | None,
) -> str:
    if content_part_text.inline_text is None and (
        content_part_text.blob is not None or content_part_text.blob_id is not None
    ):
        if blob_store is None:
            raise ValueError(
                "Blob-backed ContentPartText requires a Content service blob store."
            )
    return get_text(content_part_text, blob_store=cast(Any, blob_store))


def _source_kind(content_part_text: ContentPartText) -> str:
    if content_part_text.inline_text is not None:
        return "inline_text"
    if content_part_text.blob is not None or content_part_text.blob_id is not None:
        return "blob_text"
    return "empty_text"


def _combined_source_kind(parts: list[ContentTextPartV1]) -> str:
    kinds = {part.source_kind for part in parts}
    if not kinds:
        return "empty"
    if len(kinds) == 1:
        return next(iter(kinds))
    return "mixed"


async def _invoke_constructor(
    *,
    runtime_context: _ContentRuntimeContext,
    operation_context: ServiceOperationContext,
    branch_id: UUID,
    projection_hash: str,
    object_projection_graph_id: UUID,
    function_id: UUID,
    kwargs: dict[str, object],
    context: str,
) -> InvokeFunctionResponse:
    environment_context = _environment_invocation_context(operation_context)
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=cast(UUID, environment_context.actor_id),
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            call_target=MetaGraphFunctionCallTarget.opg_constructor,
            object_projection_graph_id=object_projection_graph_id,
            function_id=function_id,
            args=cast(JsonArray, []),
            kwargs=cast(
                JsonObject,
                {key: value for key, value in kwargs.items() if value is not None},
            ),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    _ensure_invoke_succeeded(response=response, context=context)
    return response


async def _invoke_instance(
    *,
    runtime_context: _ContentRuntimeContext,
    operation_context: ServiceOperationContext,
    branch_id: UUID,
    projection_hash: str,
    object_id: UUID,
    function_id: UUID,
    kwargs: dict[str, object],
    context: str,
) -> InvokeFunctionResponse:
    environment_context = _environment_invocation_context(operation_context)
    response = await runtime_context.graph_gateway.invoke_function(
        request=InvokeFunctionRequest(
            actor_id=cast(UUID, environment_context.actor_id),
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            call_target=MetaGraphFunctionCallTarget.instance,
            target_object_id=object_id,
            function_id=function_id,
            args=cast(JsonArray, []),
            kwargs=cast(
                JsonObject,
                {key: value for key, value in kwargs.items() if value is not None},
            ),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        ),
        graph_context=runtime_context.runtime_index,
    )
    _ensure_invoke_succeeded(response=response, context=context)
    return response


def _resolve_content_runtime_context(
    *,
    graph_gateway: ServiceGraphGateway,
    runtime_index: MetaGraphRuntimeIndex,
) -> _ContentRuntimeContext:
    content_projection, content_class_config = _resolve_projection_and_root_class(
        runtime_index=runtime_index,
        projection_name="Content",
        root_class_name="Content",
    )
    (
        content_package_projection,
        content_package_class_config,
    ) = _resolve_projection_and_root_class(
        runtime_index=runtime_index,
        projection_name="ContentPackage",
        root_class_name="ContentPackage",
    )
    content_package_content_class_config = _resolve_projection_class(
        runtime_index=runtime_index,
        projection=content_package_projection,
        class_name="ContentPackageContent",
    )
    content_package_artifact_class_config = _resolve_projection_class(
        runtime_index=runtime_index,
        projection=content_package_projection,
        class_name="ContentPackageArtifact",
    )
    function_ids = {
        "Content.create_content": _resolve_function_id(
            class_config=content_class_config,
            function_name="create_content",
        ),
        "ContentPackage.build": _resolve_function_id(
            class_config=content_package_class_config,
            function_name="build",
        ),
        "ContentPackage.attach_content": _resolve_function_id(
            class_config=content_package_class_config,
            function_name="attach_content",
        ),
        "ContentPackage.attach_artifact": _resolve_function_id(
            class_config=content_package_class_config,
            function_name="attach_artifact",
        ),
        "ContentPackageContent.build_via_content_package": _resolve_function_id(
            class_config=content_package_content_class_config,
            function_name="build_via_content_package",
        ),
        "ContentPackageArtifact.build_via_content_package": _resolve_function_id(
            class_config=content_package_artifact_class_config,
            function_name="build_via_content_package",
        ),
    }
    return _ContentRuntimeContext(
        graph_gateway=graph_gateway,
        runtime_index=runtime_index,
        content_opg_id=UUID(str(content_projection.id)),
        content_projection_hash=str(content_projection.projection_hash),
        content_package_opg_id=UUID(str(content_package_projection.id)),
        content_package_projection_hash=str(
            content_package_projection.projection_hash
        ),
        function_ids=function_ids,
    )


def _resolve_projection_and_root_class(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    projection_name: str,
    root_class_name: str,
) -> tuple[Any, Any]:
    class_configs_by_id = cast(Any, getattr(runtime_index, "class_configs_by_id", {}))
    projections = list(cast(Any, getattr(runtime_index, "opg_by_hash", {})).values())
    if not projections:
        projections = list(
            cast(
                Any,
                getattr(
                    getattr(runtime_index, "ocg", None), "object_projection_graphs", []
                ),
            )
        )

    matches: list[tuple[Any, Any]] = []
    for projection in projections:
        if (getattr(projection, "name", "") or "").strip() != projection_name:
            continue
        for node in getattr(projection, "object_projection_graph_nodes", []) or []:
            if not bool(getattr(node, "is_root", False)):
                continue
            class_config = class_configs_by_id.get(
                getattr(node, "class_config_id", None)
            )
            if class_config is None:
                continue
            if (
                getattr(class_config, "name", "") or ""
            ).strip() == root_class_name or _class_fqn(class_config).endswith(
                f".{root_class_name}"
            ):
                matches.append((projection, class_config))
    if len(matches) != 1:
        raise ValueError(
            "Content projection root is missing or ambiguous in runtime index: "
            f"projection_name={projection_name!r} root_class_name={root_class_name!r} "
            f"matches={len(matches)}"
        )
    return matches[0]


def _resolve_projection_class(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    projection: Any,
    class_name: str,
) -> Any:
    class_configs_by_id = cast(Any, getattr(runtime_index, "class_configs_by_id", {}))
    matches: list[Any] = []
    for node in getattr(projection, "object_projection_graph_nodes", []) or []:
        class_config = class_configs_by_id.get(getattr(node, "class_config_id", None))
        if class_config is None:
            continue
        if (
            getattr(class_config, "name", "") or ""
        ).strip() == class_name or _class_fqn(class_config).endswith(f".{class_name}"):
            matches.append(class_config)
    if len(matches) != 1:
        raise ValueError(
            "Content projection class is missing or ambiguous in runtime index: "
            f"projection_name={getattr(projection, 'name', '')!r} "
            f"class_name={class_name!r} matches={len(matches)}"
        )
    return matches[0]


def _resolve_function_id(*, class_config: Any, function_name: str) -> UUID:
    matches = [
        function_config.id
        for link in getattr(class_config, "class_config_function_configs", []) or []
        for function_config in [getattr(link, "function_config", None)]
        if function_config is not None
        and (getattr(function_config, "name", "") or "").strip() == function_name
    ]
    if len(matches) != 1:
        raise ValueError(
            "Content function is missing or ambiguous in runtime index: "
            f"class_fqn={_class_fqn(class_config)!r} function_name={function_name!r} "
            f"matches={len(matches)}"
        )
    return UUID(str(matches[0]))


def _function_id(
    *,
    runtime_context: _ContentRuntimeContext,
    function_name: str,
) -> UUID:
    function_id = runtime_context.function_ids.get(function_name)
    if function_id is None:
        raise ValueError(f"Content function missing from runtime context: {function_name}")
    return function_id


def _ensure_invoke_succeeded(*, response: InvokeFunctionResponse, context: str) -> None:
    if (response.status or "").strip().lower() == "succeeded":
        return
    raise ValueError(f"{context} failed: {response.error or response.status}")


def _environment_invocation_context(
    operation_context: ServiceOperationContext,
) -> _EnvironmentInvocationContext:
    host_context = current_service_api_host_context()
    environment_context = (
        host_context.environment_context if host_context is not None else None
    )
    environment_id = _uuid_or_none(getattr(environment_context, "environment_id", None))
    if environment_id is None:
        environment_id = _uuid_or_none(getattr(operation_context, "environment_id", None))
    if environment_id is None:
        environment_id = uuid5(
            _content_namespace(),
            "aware:content_service:environment:"
            f"{operation_context.branch_id}:{operation_context.projection_hash}",
        )
    actor_id = _uuid_or_none(getattr(operation_context, "actor_id", None))
    if actor_id is None:
        actor_id = _uuid_or_none(getattr(environment_context, "actor_id", None))
    if actor_id is None:
        actor_id = uuid5(
            _content_namespace(),
            "aware:content_service:actor:"
            f"{operation_context.branch_id}:{operation_context.projection_hash}",
        )
    return _EnvironmentInvocationContext(
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=_uuid_or_none(getattr(environment_context, "process_id", None))
        or _uuid_or_none(getattr(operation_context, "process_id", None)),
        thread_id=_uuid_or_none(getattr(environment_context, "thread_id", None))
        or _uuid_or_none(getattr(operation_context, "thread_id", None)),
    )


def _class_fqn(class_config: Any) -> str:
    fqn = getattr(class_config, "fqn", None)
    if fqn is not None:
        return str(fqn)
    namespace = str(getattr(class_config, "namespace", "") or "").strip()
    name = str(getattr(class_config, "name", "") or "").strip()
    return ".".join(part for part in (namespace, name) if part)


async def _commit_content_text(
    *,
    request: CommitContentTextRequest,
    support: _ContentProtocolSupport,
) -> ContentTextCommitResultV1:
    content_key = request.content_key.strip()
    source_kind = request.source_kind.strip()
    source_ref = request.source_ref.strip()
    if not content_key or not source_kind or not source_ref:
        raise ValueError(
            "commit_content_text requires non-empty content_key, source_kind, "
            "and source_ref."
        )
    ordered_parts = sorted(request.parts, key=lambda part: part.position)
    if request.text is not None and ordered_parts:
        raise ValueError("commit_content_text accepts text or parts, not both.")
    if request.text is not None:
        text = request.text
    else:
        text = "".join(part.text for part in ordered_parts)
    if not text:
        raise ValueError("commit_content_text requires non-empty text truth.")
    for part in ordered_parts:
        encoded_part = part.text.encode("utf-8")
        _validate_digest(
            expected_digest=part.digest,
            actual_digest=sha256(encoded_part).hexdigest(),
            field_name=f"parts[{part.position}].digest",
        )
        if part.size_bytes is not None and part.size_bytes != len(encoded_part):
            raise ValueError(
                f"parts[{part.position}].size_bytes does not match UTF-8 text."
            )
    encoded = text.encode("utf-8")
    digest = sha256(encoded).hexdigest()
    size_bytes = len(encoded)
    _validate_digest(
        expected_digest=request.digest,
        actual_digest=digest,
        field_name="commit_content_text.digest",
    )
    if request.size_bytes is not None and request.size_bytes != size_bytes:
        raise ValueError(
            "commit_content_text.size_bytes does not match UTF-8 text: "
            f"expected {request.size_bytes}, got {size_bytes}."
        )

    host_context = support.host_context()
    runtime_context = await support.runtime_context()
    content_branch_id = stable_content_id(key=content_key)
    response = await _invoke_constructor(
        runtime_context=runtime_context,
        operation_context=host_context.operation_context,
        branch_id=content_branch_id,
        projection_hash=runtime_context.content_projection_hash,
        object_projection_graph_id=runtime_context.content_opg_id,
        function_id=_function_id(
            runtime_context=runtime_context,
            function_name="Content.create_content",
        ),
        kwargs={
            "key": content_key,
            "title": request.title,
            "source": _enum_value(ContentSource.agent),
            "seed_inline_text": text,
            "seed_part_position": 0,
        },
        context="content.text.commit_content_text:create_content",
    )
    content_payload = _payload_dict(response.payload)
    content_id = (
        _uuid_or_none(content_payload.get("id"))
        or response.root_object_id
        or content_branch_id
    )
    commit_evidence = _service_host_content_commit_evidence(
        fallback_object_instance_graph_commit_id=(
            response.object_instance_graph_commit_id or response.domain_commit_id
        )
    )
    provenance = _json_merge(
        request.provenance,
        {
            "service_operation": "content.commit_content_text",
            "ontology_constructor": "Content.create_content",
            "function_call_id": str(response.function_call_id)
            if response.function_call_id is not None
            else None,
            "part_count": len(ordered_parts) if ordered_parts else 1,
            "domain_commit_id": str(commit_evidence.domain_commit_id)
            if commit_evidence.domain_commit_id is not None
            else None,
            "object_instance_graph_commit_id": (
                str(commit_evidence.object_instance_graph_commit_id)
                if commit_evidence.object_instance_graph_commit_id is not None
                else None
            ),
            "service_host_receipt_ref": commit_evidence.service_host_receipt_ref,
            "service_host_commit_evidence": dict(commit_evidence.metadata),
        },
    )
    return ContentTextCommitResultV1(
        content_id=content_id,
        content_key=str(content_payload.get("key") or content_key),
        title=request.title,
        source_kind=source_kind,
        source_ref=source_ref,
        media_type=request.media_type,
        digest_algorithm=request.digest_algorithm,
        digest=digest,
        size_bytes=size_bytes,
        domain_commit_id=commit_evidence.domain_commit_id,
        object_instance_graph_commit_id=(
            commit_evidence.object_instance_graph_commit_id
        ),
        service_host_receipt_ref=commit_evidence.service_host_receipt_ref,
        provenance=provenance,
    )


async def _materialize_content_package_export(
    package_export: ContentPackageExportDocumentV1,
    *,
    support: _ContentProtocolSupport,
) -> ContentPackageMaterializationResultV1:
    target_path = _normalize_relative_path(package_export.target_path)
    text = _export_text(package_export)
    encoded = text.encode("utf-8")
    digest = sha256(encoded).hexdigest()
    size_bytes = len(encoded)
    _validate_digest(
        expected_digest=package_export.digest,
        actual_digest=digest,
        field_name="package_export.digest",
    )
    if package_export.size_bytes is not None and package_export.size_bytes != size_bytes:
        raise ValueError(
            "package_export.size_bytes does not match UTF-8 content size: "
            f"expected {package_export.size_bytes}, got {size_bytes}."
        )

    artifact = _artifact_projection(
        package_export=package_export,
        target_path=target_path,
        digest=digest,
        size_bytes=size_bytes,
    )
    content_key = package_export.content_key or _default_content_key(
        source_provider_key=package_export.source_provider_key,
        source_ref=package_export.source_ref,
        target_path=target_path,
    )
    host_context = support.host_context()
    runtime_context = await support.runtime_context()
    operation_context = host_context.operation_context
    content_branch_id = stable_content_id(key=content_key)
    content_response = await _invoke_constructor(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=content_branch_id,
        projection_hash=runtime_context.content_projection_hash,
        object_projection_graph_id=runtime_context.content_opg_id,
        function_id=_function_id(
            runtime_context=runtime_context,
            function_name="Content.create_content",
        ),
        kwargs={
            "key": content_key,
            "title": package_export.content_title or package_export.title,
            "source": _enum_value(ContentSource.agent),
            "seed_inline_text": text,
            "seed_part_position": 0,
        },
        context="content.package.materialize_content_package:create_content",
    )
    content_payload = _payload_dict(content_response.payload)
    content_id = (
        _uuid_or_none(content_payload.get("id"))
        or content_response.root_object_id
        or content_branch_id
    )
    materialized_content_key = str(content_payload.get("key") or content_key)

    provider_payload = _export_provider_payload(package_export)
    content_package_branch_id = stable_content_package_id(
        package_name=package_export.package_name
    )
    content_package_response = await _invoke_constructor(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=content_package_branch_id,
        projection_hash=runtime_context.content_package_projection_hash,
        object_projection_graph_id=runtime_context.content_package_opg_id,
        function_id=_function_id(
            runtime_context=runtime_context,
            function_name="ContentPackage.build",
        ),
        kwargs={
            "package_name": package_export.package_name,
            "package_root": package_export.package_root,
            "manifest_relative_path": package_export.manifest_relative_path,
            "title": package_export.title or package_export.content_title,
            "package_kind": package_export.package_kind,
            "source_provider_key": package_export.source_provider_key,
            "source_ref": package_export.source_ref,
            "runtime_contract_version": package_export.runtime_contract_version,
            "provider_payload": provider_payload,
        },
        context="content.package.materialize_content_package:content_package",
    )
    content_package_payload = _payload_dict(content_package_response.payload)
    content_package_id = (
        _uuid_or_none(content_package_payload.get("id"))
        or content_package_response.root_object_id
        or content_package_branch_id
    )

    receipt_payload = JsonObject(
        {
            "digest_algorithm": package_export.digest_algorithm,
            "digest": digest,
            "size_bytes": size_bytes,
            "target_path": target_path,
            "contract_version": package_export.contract_version,
        }
    )
    content_package_content_response = await _invoke_instance(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=content_package_id,
        projection_hash=runtime_context.content_package_projection_hash,
        object_id=content_package_id,
        function_id=_function_id(
            runtime_context=runtime_context,
            function_name="ContentPackage.attach_content",
        ),
        kwargs={
            "content_id": content_id,
            "relative_path": target_path,
            "content_role": artifact.artifact_role or "content",
            "position": 0,
            "media_type": package_export.media_type,
            "title": package_export.content_title or package_export.title,
            "source_ref": package_export.source_ref,
            "provider_payload": provider_payload,
            "receipt_payload": receipt_payload,
        },
        context="content.package.materialize_content_package:package_content",
    )
    content_package_artifact_response = await _invoke_instance(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=content_package_id,
        projection_hash=runtime_context.content_package_projection_hash,
        object_id=content_package_id,
        function_id=_function_id(
            runtime_context=runtime_context,
            function_name="ContentPackage.attach_artifact",
        ),
        kwargs={
            "output_key": artifact.output_key,
            "artifact_key": artifact.artifact_key,
            "status": _enum_value(ContentPackageArtifactStatus.available),
            "artifact_family": artifact.artifact_family,
            "artifact_role": artifact.artifact_role,
            "required_for": artifact.required_for,
            "producer_provider_key": artifact.producer_provider_key,
            "producer_key": artifact.producer_key,
            "producer_kind": artifact.producer_kind,
            "materialization_index": artifact.materialization_index,
            "digest": digest,
            "digest_algorithm": package_export.digest_algorithm,
            "relative_path": target_path,
            "uri": artifact.uri,
            "media_type": package_export.media_type,
            "size_bytes": size_bytes,
            "runtime_contract_version": artifact.runtime_contract_version,
            "provider_payload": artifact.provider_payload,
            "receipt_payload": artifact.receipt_payload or receipt_payload,
        },
        context="content.package.materialize_content_package:package_artifact",
    )

    object_instance_graph_commit_id = (
        content_package_artifact_response.object_instance_graph_commit_id
        or content_package_artifact_response.domain_commit_id
        or content_package_content_response.object_instance_graph_commit_id
        or content_package_content_response.domain_commit_id
        or content_package_response.object_instance_graph_commit_id
        or content_package_response.domain_commit_id
    )
    commit_evidence = _service_host_content_commit_evidence(
        fallback_object_instance_graph_commit_id=object_instance_graph_commit_id,
    )
    artifact_ref = ContentPackageMaterializedArtifactRefV1(
        content_package_id=content_package_id,
        content_id=content_id,
        domain_commit_id=commit_evidence.domain_commit_id,
        object_instance_graph_commit_id=commit_evidence.object_instance_graph_commit_id,
        service_host_receipt_ref=commit_evidence.service_host_receipt_ref,
        output_key=artifact.output_key,
        artifact_key=artifact.artifact_key,
        status="available",
        artifact_family=artifact.artifact_family,
        artifact_role=artifact.artifact_role,
        required_for=artifact.required_for,
        producer_provider_key=artifact.producer_provider_key,
        producer_key=artifact.producer_key,
        producer_kind=artifact.producer_kind,
        materialization_index=artifact.materialization_index,
        digest_algorithm=package_export.digest_algorithm,
        digest=digest,
        relative_path=target_path,
        uri=artifact.uri,
        media_type=package_export.media_type,
        size_bytes=size_bytes,
        runtime_contract_version=artifact.runtime_contract_version,
        provider_payload=artifact.provider_payload,
        receipt_payload=artifact.receipt_payload or receipt_payload,
    )
    provenance = _json_merge(
        package_export.provenance,
        {
            "service_operation": "content.materialize_content_package",
            "ontology_constructor_sequence": [
                "Content.create_content",
                "ContentPackage.build",
                "ContentPackage.attach_content",
                "ContentPackage.attach_artifact",
            ],
            "object_instance_graph_commit_id": (
                str(commit_evidence.object_instance_graph_commit_id)
                if commit_evidence.object_instance_graph_commit_id is not None
                else None
            ),
            "domain_commit_id": (
                str(commit_evidence.domain_commit_id)
                if commit_evidence.domain_commit_id is not None
                else None
            ),
            "service_host_receipt_ref": commit_evidence.service_host_receipt_ref,
            "service_host_commit_evidence": dict(commit_evidence.metadata),
            "function_call_ids": {
                "content": str(content_response.function_call_id)
                if content_response.function_call_id is not None
                else None,
                "content_package": str(content_package_response.function_call_id)
                if content_package_response.function_call_id is not None
                else None,
                "content_package_content": str(
                    content_package_content_response.function_call_id
                )
                if content_package_content_response.function_call_id is not None
                else None,
                "content_package_artifact": str(
                    content_package_artifact_response.function_call_id
                )
                if content_package_artifact_response.function_call_id is not None
                else None,
            },
            "object_instance_graph_commit_capture": (
                "service_host_context"
                if commit_evidence.has_any
                else "unavailable_without_service_host_commit_evidence"
            ),
        },
    )
    return ContentPackageMaterializationResultV1(
        content_package_id=content_package_id,
        content_id=content_id,
        domain_commit_id=commit_evidence.domain_commit_id,
        object_instance_graph_commit_id=commit_evidence.object_instance_graph_commit_id,
        service_host_receipt_ref=commit_evidence.service_host_receipt_ref,
        package_name=package_export.package_name,
        content_key=materialized_content_key,
        source_provider_key=package_export.source_provider_key,
        source_ref=package_export.source_ref,
        target_path=target_path,
        media_type=package_export.media_type,
        digest_algorithm=package_export.digest_algorithm,
        digest=digest,
        size_bytes=size_bytes,
        artifact_refs=[artifact_ref],
        aware_content_mapping=package_export.aware_content_mapping,
        provenance=provenance,
    )


def _service_host_content_commit_evidence(
    *,
    fallback_object_instance_graph_commit_id: UUID | None = None,
) -> _ContentCommitEvidence:
    host_context = current_service_api_host_context()
    if host_context is None:
        return _ContentCommitEvidence(
            object_instance_graph_commit_id=fallback_object_instance_graph_commit_id,
            metadata=JsonObject(
                {
                    "source": "service_host_context",
                    "available": False,
                    "reason": "no_active_service_api_host_context",
                    "fallback_object_instance_graph_commit_id": (
                        str(fallback_object_instance_graph_commit_id)
                        if fallback_object_instance_graph_commit_id is not None
                        else None
                    ),
                }
            )
        )

    invocation_context = _mapping_payload(host_context.invocation_context)
    receipt_payload = _first_mapping_payload(
        invocation_context,
        (
            "service_api_dispatch_receipt",
            "api_dispatch_receipt",
            "dispatch_receipt",
            "service_host_receipt",
            "receipt",
        ),
    )
    domain_commit_id = _first_uuid(
        invocation_context,
        (
            "domain_commit_id",
            "content_package_domain_commit_id",
            "service_operation_commit_id",
            "api_call_outcome_commit_id",
        ),
    ) or _first_uuid(
        receipt_payload,
        (
            "domain_commit_id",
            "service_operation_commit_id",
            "api_call_outcome_commit_id",
        ),
    )
    object_instance_graph_commit_id = _first_uuid(
        invocation_context,
        (
            "object_instance_graph_commit_id",
            "content_package_object_instance_graph_commit_id",
        ),
    ) or _first_uuid(
        receipt_payload,
        ("object_instance_graph_commit_id",),
    ) or fallback_object_instance_graph_commit_id
    service_host_receipt_ref = _first_text(
        invocation_context,
        (
            "service_host_receipt_ref",
            "receipt_ref",
            "api_dispatch_receipt_ref",
        ),
    ) or _first_text(
        receipt_payload,
        (
            "service_host_receipt_ref",
            "receipt_ref",
            "api_dispatch_receipt_ref",
        ),
    )
    if service_host_receipt_ref is None:
        service_host_receipt_ref = _service_host_receipt_ref(receipt_payload)

    metadata = cast(
        JsonObject,
        {
            "source": "service_host_context",
            "available": True,
            "service_name": host_context.service_name,
            "service_package_id": (
                str(host_context.service_package_id)
                if host_context.service_package_id is not None
                else None
            ),
            "service_package_name": host_context.service_package_name,
            "operation_context": _json_safe(
                _model_payload(host_context.operation_context)
            ),
            "receipt": _json_safe(receipt_payload) if receipt_payload else None,
            "evidence_fields": {
                "domain_commit_id": str(domain_commit_id)
                if domain_commit_id is not None
                else None,
                "object_instance_graph_commit_id": (
                    str(object_instance_graph_commit_id)
                    if object_instance_graph_commit_id is not None
                    else None
                ),
                "service_host_receipt_ref": service_host_receipt_ref,
            },
            "fallback_object_instance_graph_commit_id": (
                str(fallback_object_instance_graph_commit_id)
                if fallback_object_instance_graph_commit_id is not None
                else None
            ),
        },
    )
    return _ContentCommitEvidence(
        domain_commit_id=domain_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        service_host_receipt_ref=service_host_receipt_ref,
        metadata=metadata,
    )


def _export_text(package_export: ContentPackageExportDocumentV1) -> str:
    if package_export.content_text is not None:
        return package_export.content_text
    text_parts = [
        part.text
        for part in sorted(package_export.parts, key=lambda value: value.position)
        if part.content_part_type == "text" and part.text is not None
    ]
    if not text_parts:
        raise ValueError(
            "materialize_content_package requires content_text or text parts."
        )
    return "".join(text_parts)


def _artifact_projection(
    *,
    package_export: ContentPackageExportDocumentV1,
    target_path: str,
    digest: str,
    size_bytes: int,
) -> ContentPackageArtifactProjectionV1:
    artifact = package_export.artifact
    if artifact is not None:
        relative_path = _normalize_relative_path(artifact.relative_path)
        if relative_path != target_path:
            raise ValueError(
                "package_export.artifact.relative_path must match target_path: "
                f"{relative_path!r} != {target_path!r}."
            )
        _validate_digest(
            expected_digest=artifact.digest,
            actual_digest=digest,
            field_name="package_export.artifact.digest",
        )
        if artifact.size_bytes is not None and artifact.size_bytes != size_bytes:
            raise ValueError(
                "package_export.artifact.size_bytes does not match UTF-8 "
                f"content size: expected {artifact.size_bytes}, got {size_bytes}."
            )
        return artifact
    return ContentPackageArtifactProjectionV1(
        artifact_key=target_path,
        producer_provider_key=package_export.source_provider_key,
        producer_key=f"{package_export.source_provider_key}_content_export",
        relative_path=target_path,
        media_type=package_export.media_type,
        digest_algorithm=package_export.digest_algorithm,
        digest=digest,
        size_bytes=size_bytes,
        runtime_contract_version=package_export.runtime_contract_version,
        provider_payload=package_export.provider_payload,
        receipt_payload=JsonObject(
            {
                "digest_algorithm": package_export.digest_algorithm,
                "digest": digest,
                "size_bytes": size_bytes,
            }
        ),
    )


def _normalize_relative_path(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("relative content path must be non-empty.")
    path = PurePosixPath(stripped)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"relative content path is not workspace-safe: {value!r}.")
    return path.as_posix()


def _validate_digest(
    *,
    expected_digest: str | None,
    actual_digest: str,
    field_name: str,
) -> None:
    if expected_digest is None:
        return
    normalized = expected_digest.removeprefix("sha256:")
    if normalized != actual_digest:
        raise ValueError(
            f"{field_name} does not match UTF-8 content digest: "
            f"expected {expected_digest}, got {actual_digest}."
        )


def _default_content_key(
    *,
    source_provider_key: str,
    source_ref: str,
    target_path: str,
) -> str:
    return f"{source_provider_key}:{source_ref}:{target_path}"


def _export_provider_payload(
    package_export: ContentPackageExportDocumentV1,
) -> JsonObject:
    return _json_merge(
        package_export.provider_payload,
        {
            "export_kind": package_export.export_kind,
            "contract_version": package_export.contract_version,
            "aware_content_mapping": dict(package_export.aware_content_mapping),
            "parts": [
                part.model_dump(mode="json", exclude_none=True)
                for part in package_export.parts
            ],
            "provenance": dict(package_export.provenance),
        },
    )


def _json_merge(base: JsonObject, overlay: dict[str, object]) -> JsonObject:
    merged: dict[str, object] = dict(base)
    merged.update(overlay)
    return cast(JsonObject, merged)


def _payload_dict(value: object | None) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    nested = value.get("value")
    if isinstance(nested, Mapping):
        return dict(nested)
    return dict(value)


def _enum_value(value: object) -> object:
    raw = getattr(value, "value", None)
    if raw is None:
        return value
    return raw


def _mapping_payload(value: object) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    payload = _model_payload(value)
    if isinstance(payload, Mapping):
        return dict(payload)
    return {}


def _first_mapping_payload(
    payload: Mapping[str, object],
    keys: tuple[str, ...],
) -> dict[str, object]:
    for key in keys:
        nested = _mapping_payload(payload.get(key))
        if nested:
            return nested
    return {}


def _model_payload(value: object) -> object:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json", exclude_none=True)
    return value


def _first_uuid(payload: Mapping[str, object], keys: tuple[str, ...]) -> UUID | None:
    for key in keys:
        resolved = _uuid_or_none(payload.get(key))
        if resolved is not None:
            return resolved
    return None


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if value is None or value == "":
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _first_text(payload: Mapping[str, object], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = _optional_text(payload.get(key))
        if value is not None:
            return value
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _service_host_receipt_ref(payload: Mapping[str, object]) -> str | None:
    for prefix, key in (
        ("service-host", "network_request_id"),
        ("service-api-call", "api_call_id"),
        ("service-operation-commit", "service_operation_commit_id"),
        ("api-call-outcome-commit", "api_call_outcome_commit_id"),
    ):
        value = _optional_text(payload.get(key))
        if value is not None:
            return f"{prefix}:{value}"
    return None


def _json_safe(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, tuple | list):
        return [_json_safe(item) for item in value if item is not None]
    if value is None or isinstance(value, bool | int | float | str):
        return value
    raw = getattr(value, "value", None)
    if raw is None:
        return str(value)
    return _json_safe(raw)


def _content_namespace() -> UUID:
    return uuid5(NAMESPACE_URL, "aware://content/v1")


__all__ = [
    "build_aware_content_service_protocol_handler",
]
