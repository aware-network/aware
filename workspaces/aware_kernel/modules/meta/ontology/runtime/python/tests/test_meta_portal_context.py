from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_code.types import JsonArray
from aware_meta.graph.projection.branching import stable_portal_target_branch_id
from aware_meta.graph.projection.portal_index import (
    ObjectProjectionGraphPortal,
    ObjectProjectionGraphPortalIndex,
)
from aware_meta.runtime.graph_commit_invocation_backend import (
    resolve_meta_graph_object_projection_graph_identity_id,
)
from aware_meta.runtime.handler_executor.execution_context import (
    MetaGraphHandlerContext,
    MetaGraphHandlerExecutionContext,
    scoped_meta_graph_handler_execution_context,
)
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.runtime.portal_context import (
    MetaCurrentHandlerPortalClient,
    MetaPortalPendingConstructorRequest,
    current_meta_portal_source_frame,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.session.session import Session


class SourceModel(ORMModel):
    pass


def _bind_model_class_config(
    *,
    model_cls: type[ORMModel],
    class_config_id: UUID,
) -> None:
    setattr(
        cast(Any, model_cls),
        "_class_config",
        SimpleNamespace(
            id=class_config_id,
            class_config_relationships=[],
            class_config_attribute_configs=[],
        ),
    )


def _portal_index(
    *,
    portal: ObjectProjectionGraphPortal,
) -> ObjectProjectionGraphPortalIndex:
    rel_id = portal.class_config_relationship_id
    return ObjectProjectionGraphPortalIndex(
        portals=[portal],
        portals_by_source_projection_hash={portal.source_projection_hash: [portal]},
        portals_by_source_projection_hash_and_relationship_id={
            portal.source_projection_hash: {rel_id: [portal]}
        },
        reference_attribute_config_id_by_relationship_id={
            rel_id: portal.reference_attribute_config_id,
        },
        reference_field_name_by_relationship_id={rel_id: portal.reference_field_name},
    )


def _portal(
    *,
    source_class_config_id: UUID,
    target_class_config_id: UUID | None = None,
    target_object_projection_graph_id: UUID | None = None,
) -> ObjectProjectionGraphPortal:
    return ObjectProjectionGraphPortal(
        object_projection_graph_relationship_id=uuid4(),
        source_object_projection_graph_id=uuid4(),
        source_projection_hash="sha256:source",
        target_object_projection_graph_id=(
            target_object_projection_graph_id or uuid4()
        ),
        target_projection_hash="sha256:target",
        class_config_relationship_id=uuid4(),
        source_class_config_id=source_class_config_id,
        target_class_config_id=target_class_config_id or uuid4(),
        reference_attribute_config_id=uuid4(),
        reference_field_name="targets",
    )


def _client(
    *,
    portal: ObjectProjectionGraphPortal,
    index: object | None = None,
    invoke_function: object | None = None,
) -> MetaCurrentHandlerPortalClient:
    return MetaCurrentHandlerPortalClient(
        ctx=MetaGraphHandlerContext(
            requester_id=uuid4(),
            branch_id=uuid4(),
            projection_hash=portal.source_projection_hash,
            domain_object_instance_graph_id=uuid4(),
        ),
        index=cast(
            Any,
            index or SimpleNamespace(portal_index=_portal_index(portal=portal)),
        ),
        invoke_function=cast(Any, invoke_function),
    )


def _index_for_portal_constructor(
    *,
    portal: ObjectProjectionGraphPortal,
    function_id: UUID,
) -> object:
    function_config = SimpleNamespace(id=function_id, name="create")
    class_config = SimpleNamespace(
        id=portal.target_class_config_id,
        class_config_function_configs=[
            SimpleNamespace(function_config=function_config)
        ],
    )
    target_opg = SimpleNamespace(
        id=portal.target_object_projection_graph_id,
        name="Target",
        projection_hash=portal.target_projection_hash,
    )
    return SimpleNamespace(
        ocg=SimpleNamespace(
            name="Aware Tests",
            fqn_prefix="aware.tests",
            object_config_graph_identity=None,
            object_config_graph_nodes=[],
        ),
        class_configs_by_id={portal.target_class_config_id: class_config},
        opg_by_hash={portal.target_projection_hash: target_opg},
        opg_by_id={portal.target_object_projection_graph_id: target_opg},
        portal_index=_portal_index(portal=portal),
    )


def test_meta_portal_client_resolves_model_field() -> None:
    source_class_config_id = uuid4()
    portal = _portal(source_class_config_id=source_class_config_id)
    _bind_model_class_config(
        model_cls=SourceModel,
        class_config_id=source_class_config_id,
    )

    client = _client(portal=portal)

    assert (
        client.portal_for_model_field(
            orm_model=SourceModel(id=uuid4()),
            reference_field_name="targets",
        )
        == portal
    )


@pytest.mark.asyncio
async def test_meta_portal_client_invokes_pending_constructor_with_meta_backend() -> (
    None
):
    source_class_config_id = uuid4()
    target_class_config_id = uuid4()
    portal = _portal(
        source_class_config_id=source_class_config_id,
        target_class_config_id=target_class_config_id,
    )
    _bind_model_class_config(
        model_cls=SourceModel,
        class_config_id=source_class_config_id,
    )
    observed: dict[str, object] = {}
    target_object_id = uuid4()
    function_id = uuid4()
    index = _index_for_portal_constructor(
        portal=portal,
        function_id=function_id,
    )

    async def invoke_function(
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphCommitReceipt:
        observed["request"] = request
        return MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            payload={"ok": True},
            error=None,
            logs=(),
            execution_time_ms=1,
            root_object_id=target_object_id,
            graph_hash_pre=None,
            graph_hash_post="sha256:post",
            changes=JsonArray([]),
            function_call_id=uuid4(),
            function_call_response_id=uuid4(),
            commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
        )

    client = _client(
        portal=portal,
        index=index,
        invoke_function=invoke_function,
    )

    result = await client.invoke_constructor_from_pending_field(
        MetaPortalPendingConstructorRequest(
            orm_class=SourceModel,
            source_instance_id=uuid4(),
            source_object_id=uuid4(),
            reference_field_name="targets",
            function_name="create",
            payload={"value": "ok"},
            target_object_id=target_object_id,
        )
    )

    assert getattr(result, "status") == "succeeded"
    invoke_request = cast(MetaGraphInvokeFunctionInput, observed["request"])
    assert invoke_request.function_id == function_id
    assert invoke_request.call_target is MetaGraphCallTarget.opg_constructor
    assert invoke_request.domain_projection_hash == portal.target_projection_hash
    assert invoke_request.object_projection_graph_id == (
        portal.target_object_projection_graph_id
    )
    assert invoke_request.target_object_id == target_object_id
    assert invoke_request.kwargs["value"] == "ok"
    target_opg = cast(Any, index).opg_by_hash[portal.target_projection_hash]
    target_opgi_id = resolve_meta_graph_object_projection_graph_identity_id(
        index=cast(Any, index),
        opg=target_opg,
    )
    assert invoke_request.domain_branch_id == stable_portal_target_branch_id(
        object_instance_graph_id=client.ctx.domain_object_instance_graph_id,
        object_projection_graph_identity_id=target_opgi_id,
        target_object_id=target_object_id,
    )


def test_current_meta_portal_source_frame_maps_meta_handler_context() -> None:
    expected_instance_id = uuid4()
    expected_class_config_id = uuid4()
    expected_branch_id = uuid4()
    expected_oigb_id = uuid4()
    execution_context = MetaGraphHandlerExecutionContext(
        session=Session(branch_id=expected_branch_id, skip_db=True),
        ctx=MetaGraphHandlerContext(
            requester_id=uuid4(),
            domain_oigb_id=expected_oigb_id,
            branch_id=expected_branch_id,
            projection_hash="sha256:source",
        ),
        function_call=cast(Any, SimpleNamespace()),
        index=cast(Any, SimpleNamespace()),
        request=cast(
            Any,
            SimpleNamespace(
                execution_plan=SimpleNamespace(
                    target_object_id=expected_instance_id,
                    implementation=SimpleNamespace(
                        owner_class_config=SimpleNamespace(
                            id=expected_class_config_id,
                        ),
                    ),
                ),
                request=SimpleNamespace(target_object_id=None),
            ),
        ),
    )

    with scoped_meta_graph_handler_execution_context(execution_context):
        frame = current_meta_portal_source_frame()

    assert frame is not None
    assert frame.instance_id == expected_instance_id
    assert frame.source_object_id == expected_instance_id
    assert frame.class_config_id == expected_class_config_id
    assert frame.domain_oigb_id == expected_oigb_id
    assert frame.branch_id == expected_branch_id
    assert frame.projection_hash == "sha256:source"
