from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from aware_meta.graph.projection.portal_index import ObjectProjectionGraphPortal
from aware_meta.runtime.handler_context import (
    current_handler_context,
    current_handler_index,
    current_handler_invoke_function,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.handler_executor.execution_context import (
    MetaGraphHandlerContext,
    current_meta_graph_handler_execution_context_or_none,
)
from aware_meta.runtime.invocation_engine import MetaGraphInvokeFunctionCallable
from aware_meta.runtime.portal_invocation import (
    MetaPortalConstructorAuthorization,
    MetaPortalConstructorInvocationRequest,
    invoke_meta_portal_constructor,
)
from aware_orm.models.orm_model import ORMModel


@dataclass(frozen=True, slots=True)
class MetaPortalSourceFrame:
    class_config_id: UUID | None
    instance_id: UUID | None
    source_object_id: UUID | None = None
    domain_oigb_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None


@dataclass(frozen=True, slots=True)
class MetaPortalModelFieldRequest:
    orm_model: ORMModel
    reference_field_name: str


@dataclass(frozen=True, slots=True)
class MetaPortalPendingConstructorRequest:
    orm_class: type[ORMModel]
    source_instance_id: UUID
    source_object_id: UUID | None
    reference_field_name: str
    function_name: str
    payload: Mapping[str, object] | object
    target_object_id: UUID
    target_branch_id: UUID | None = None
    commit: bool | None = None


@dataclass(frozen=True, slots=True)
class MetaCurrentHandlerPortalClient:
    ctx: MetaGraphHandlerContext
    index: MetaGraphRuntimeIndex
    invoke_function: MetaGraphInvokeFunctionCallable | None = None

    def portal_for_model_field(
        self,
        *,
        orm_model: ORMModel,
        reference_field_name: str,
    ) -> ObjectProjectionGraphPortal:
        return self.portal_for_class_field(
            orm_class=type(orm_model),
            reference_field_name=reference_field_name,
            source_class_config_id=_model_class_config_id(orm_model=orm_model),
        )

    def portal_for_class_field(
        self,
        *,
        orm_class: type[ORMModel],
        reference_field_name: str,
        source_class_config_id: UUID | None = None,
    ) -> ObjectProjectionGraphPortal:
        if self.ctx.projection_hash is None:
            raise RuntimeError(
                "Meta portal context requires projection_hash in handler context"
            )

        resolved_source_cc_id = source_class_config_id
        if resolved_source_cc_id is None:
            class_config = orm_class.get_class_config()
            if class_config is None or getattr(class_config, "id", None) is None:
                raise RuntimeError(
                    "ORM class missing ClassConfig binding for Meta portal resolution: "
                    f"class={orm_class.__module__}.{orm_class.__name__}"
                )
            resolved_source_cc_id = cast(UUID, class_config.id)

        portals = (
            self.index.portal_index.portals_by_source_projection_hash.get(
                self.ctx.projection_hash,
            )
            or []
        )
        candidates = [
            portal
            for portal in portals
            if portal.source_class_config_id == resolved_source_cc_id
            and portal.reference_field_name == reference_field_name
        ]
        if not candidates:
            raise RuntimeError(
                "No Meta portal registered for model field: "
                f"source_projection_hash={self.ctx.projection_hash} "
                f"source_class_config_id={resolved_source_cc_id} "
                f"reference_field_name={reference_field_name}"
            )
        if len(candidates) != 1:
            targets = ", ".join(
                sorted({candidate.target_projection_hash for candidate in candidates})
            )
            raise RuntimeError(
                "Ambiguous Meta portal resolution: "
                f"source_projection_hash={self.ctx.projection_hash} "
                f"source_class_config_id={resolved_source_cc_id} "
                f"reference_field_name={reference_field_name} targets=[{targets}]"
            )
        return candidates[0]

    async def invoke_constructor_from_pending_field(
        self,
        request: MetaPortalPendingConstructorRequest,
    ) -> object:
        portal = self.portal_for_class_field(
            orm_class=request.orm_class,
            reference_field_name=request.reference_field_name,
        )
        authorization = _build_portal_constructor_authorization(
            ctx=self.ctx,
            orm_class=request.orm_class,
            source_instance_id=request.source_instance_id,
            source_object_id=request.source_object_id,
            class_config_relationship_id=portal.class_config_relationship_id,
            allowed_target_object_ids=frozenset({request.target_object_id}),
        )
        return await self.invoke_constructor(
            target_projection_hash=portal.target_projection_hash,
            target_object_projection_graph_id=(
                portal.target_object_projection_graph_id
            ),
            target_class_config_id=portal.target_class_config_id,
            function_name=request.function_name,
            payload=request.payload,
            target_branch_id=request.target_branch_id,
            target_object_id=request.target_object_id,
            authorization=authorization,
            commit=request.commit,
        )

    async def invoke_constructor(
        self,
        *,
        target_projection_hash: str,
        target_object_projection_graph_id: UUID,
        target_class_config_id: UUID,
        function_name: str,
        payload: Mapping[str, object] | object,
        target_branch_id: UUID | None = None,
        target_object_id: UUID | None = None,
        authorization: MetaPortalConstructorAuthorization | None = None,
        commit: bool | None = None,
    ) -> object:
        if self.ctx.projection_hash is None:
            raise RuntimeError(
                "Meta portal constructor invocation requires projection_hash"
            )
        if target_projection_hash == self.ctx.projection_hash:
            raise RuntimeError(
                "Meta portal constructor invocation target is the current lane"
            )
        if target_object_id is None:
            raise RuntimeError(
                "Meta portal constructor invocation requires target_object_id"
            )
        if authorization is None:
            raise RuntimeError(
                "Meta portal constructor invocation requires source-field "
                "authorization; use invoke_constructor_from_pending_field"
            )

        return await invoke_meta_portal_constructor(
            MetaPortalConstructorInvocationRequest(
                ctx=self.ctx,
                index=self.index,
                invoke_function=self.invoke_function,
                target_projection_hash=target_projection_hash,
                target_object_projection_graph_id=(target_object_projection_graph_id),
                target_class_config_id=target_class_config_id,
                function_name=function_name,
                payload=payload,
                target_branch_id=target_branch_id,
                target_object_id=target_object_id,
                authorization=authorization,
                commit=commit,
            )
        )


def current_handler_portal_client() -> MetaCurrentHandlerPortalClient:
    return MetaCurrentHandlerPortalClient(
        ctx=current_handler_context(),
        index=current_handler_index(),
        invoke_function=current_handler_invoke_function(),
    )


def current_meta_portal_source_frame() -> MetaPortalSourceFrame | None:
    execution_context = current_meta_graph_handler_execution_context_or_none()
    if execution_context is None:
        return None
    ctx = execution_context.ctx
    request = execution_context.request
    class_config_id = None
    instance_id = None
    if request is not None:
        owner_class_config = request.execution_plan.implementation.owner_class_config
        if owner_class_config is not None:
            class_config_id = owner_class_config.id
        instance_id = (
            request.execution_plan.target_object_id or request.request.target_object_id
        )
    return MetaPortalSourceFrame(
        class_config_id=class_config_id,
        instance_id=instance_id,
        source_object_id=instance_id,
        domain_oigb_id=ctx.domain_oigb_id,
        branch_id=ctx.branch_id,
        projection_hash=ctx.projection_hash,
    )


def _model_class_config_id(*, orm_model: ORMModel) -> UUID:
    class_config = type(orm_model).get_class_config()
    if class_config is None or getattr(class_config, "id", None) is None:
        raise RuntimeError(
            "ORM model missing ClassConfig binding for Meta portal resolution: "
            f"class={type(orm_model).__module__}.{type(orm_model).__name__}"
        )
    return cast(UUID, class_config.id)


def _build_portal_constructor_authorization(
    *,
    ctx: MetaGraphHandlerContext,
    orm_class: type[ORMModel],
    source_instance_id: UUID,
    source_object_id: UUID | None,
    class_config_relationship_id: UUID,
    allowed_target_object_ids: frozenset[UUID],
) -> MetaPortalConstructorAuthorization:
    class_config = orm_class.get_class_config()
    if class_config is None or getattr(class_config, "id", None) is None:
        raise RuntimeError(
            "ORM class missing ClassConfig binding for Meta portal source: "
            f"class={orm_class.__module__}.{orm_class.__name__}"
        )
    source_class_config_id = cast(UUID, class_config.id)
    if ctx.branch_id is None:
        raise RuntimeError(
            "Meta portal constructor source authorization requires branch_id"
        )
    if ctx.projection_hash is None:
        raise RuntimeError(
            "Meta portal constructor source authorization requires projection_hash"
        )
    return MetaPortalConstructorAuthorization(
        source_class_config_id=source_class_config_id,
        source_instance_id=source_instance_id,
        source_object_id=source_object_id,
        source_branch_id=ctx.branch_id,
        source_projection_hash=ctx.projection_hash,
        class_config_relationship_id=class_config_relationship_id,
        allowed_target_object_ids=allowed_target_object_ids,
    )


__all__ = [
    "MetaCurrentHandlerPortalClient",
    "MetaPortalModelFieldRequest",
    "MetaPortalPendingConstructorRequest",
    "MetaPortalSourceFrame",
    "current_handler_portal_client",
    "current_meta_portal_source_frame",
]
