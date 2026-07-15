from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_code.types import JsonArray
from aware_meta.graph.projection.branching import stable_portal_target_branch_id
from aware_meta.runtime import portal_invocation as portal_invocation_mod
from aware_meta.runtime.graph_commit_invocation_backend import (
    resolve_meta_graph_object_projection_graph_identity_id,
)
from aware_meta.runtime.handler_executor.execution_context import (
    MetaGraphHandlerContext,
)
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.runtime.portal_invocation import (
    MetaPortalConstructorAuthorization,
    MetaPortalConstructorInvocationRequest,
    invoke_meta_portal_constructor,
)


def _index(*, target_class_config_id: UUID, target_function_id: UUID) -> Any:
    function_config = SimpleNamespace(id=target_function_id, name="create")
    target_class = SimpleNamespace(
        id=target_class_config_id,
        class_config_function_configs=[
            SimpleNamespace(function_config=function_config)
        ],
    )
    target_opg = SimpleNamespace(
        id=uuid4(),
        projection_hash="sha256:target",
    )
    return SimpleNamespace(
        ocg=SimpleNamespace(
            name="Aware Tests",
            fqn_prefix="aware.tests",
            object_config_graph_identity=None,
            object_config_graph_nodes=[],
        ),
        class_configs_by_id={target_class_config_id: target_class},
        opg_by_hash={target_opg.projection_hash: target_opg},
    )


def _request(
    *,
    index: Any,
    invoke_function: Any,
    target_class_config_id: UUID,
    source_oig_id: UUID,
    source_branch_id: UUID,
    source_projection_hash: str = "sha256:source",
    target_object_id: UUID | None = None,
    commit: bool | None = True,
) -> MetaPortalConstructorInvocationRequest:
    target_opg = next(iter(index.opg_by_hash.values()))
    target_object_id = target_object_id or uuid4()
    return MetaPortalConstructorInvocationRequest(
        ctx=MetaGraphHandlerContext(
            requester_id=uuid4(),
            domain_oigb_id=uuid4(),
            domain_object_instance_graph_id=source_oig_id,
            domain_object_instance_graph_identity_id=uuid4(),
            branch_id=source_branch_id,
            projection_hash=source_projection_hash,
        ),
        index=index,
        invoke_function=invoke_function,
        target_projection_hash=target_opg.projection_hash,
        target_object_projection_graph_id=target_opg.id,
        target_class_config_id=target_class_config_id,
        function_name="create",
        payload={"value": "ok"},
        target_object_id=target_object_id,
        authorization=MetaPortalConstructorAuthorization(
            source_class_config_id=uuid4(),
            source_instance_id=uuid4(),
            source_object_id=uuid4(),
            source_branch_id=source_branch_id,
            source_projection_hash=source_projection_hash,
            class_config_relationship_id=uuid4(),
            allowed_target_object_ids=frozenset({target_object_id}),
        ),
        commit=commit,
    )


def _expected_target_branch_id(
    *,
    index: Any,
    source_oig_id: UUID,
    target_object_id: UUID,
) -> UUID:
    target_opg = next(iter(index.opg_by_hash.values()))
    target_opgi_id = resolve_meta_graph_object_projection_graph_identity_id(
        index=cast(Any, index),
        opg=target_opg,
    )
    return stable_portal_target_branch_id(
        object_instance_graph_id=source_oig_id,
        object_projection_graph_identity_id=target_opgi_id,
        target_object_id=target_object_id,
    )


@pytest.mark.asyncio
async def test_committed_portal_constructor_attaches_oigb_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_class_config_id = uuid4()
    target_function_id = uuid4()
    index = _index(
        target_class_config_id=target_class_config_id,
        target_function_id=target_function_id,
    )
    source_oig_id = uuid4()
    source_branch_id = uuid4()
    target_object_id = uuid4()
    expected_branch_id = _expected_target_branch_id(
        index=index,
        source_oig_id=source_oig_id,
        target_object_id=target_object_id,
    )
    observed_requests: list[MetaGraphInvokeFunctionInput] = []
    attach_calls: list[dict[str, object]] = []

    async def invoke_function(
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphCommitReceipt:
        observed_requests.append(request)
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

    async def attach_oigb_relationship(**kwargs: object) -> None:
        attach_calls.append(dict(kwargs))

    monkeypatch.setattr(
        portal_invocation_mod,
        "attach_oigb_relationship",
        attach_oigb_relationship,
    )

    request = _request(
        index=index,
        invoke_function=invoke_function,
        target_class_config_id=target_class_config_id,
        source_oig_id=source_oig_id,
        source_branch_id=source_branch_id,
        target_object_id=target_object_id,
    )
    result = await invoke_meta_portal_constructor(request)

    assert result.status == "succeeded"
    assert result.branch_id == expected_branch_id
    assert observed_requests[0].call_target is MetaGraphCallTarget.opg_constructor
    assert attach_calls == [
        {
            "index": index,
            "author_id": request.ctx.requester_id,
            "source_domain_branch_id": source_branch_id,
            "source_projection_hash": request.authorization.source_projection_hash,
            "target_domain_branch_id": expected_branch_id,
            "target_projection_hash": request.target_projection_hash,
        }
    ]


@pytest.mark.asyncio
async def test_non_committed_portal_constructor_does_not_attach_oigb_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_class_config_id = uuid4()
    target_function_id = uuid4()
    index = _index(
        target_class_config_id=target_class_config_id,
        target_function_id=target_function_id,
    )
    source_oig_id = uuid4()
    source_branch_id = uuid4()
    target_object_id = uuid4()
    attach_calls: list[dict[str, object]] = []

    async def invoke_function(
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphCommitReceipt:
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
            commit_id=None,
            object_instance_graph_commit_id=None,
        )

    async def attach_oigb_relationship(**kwargs: object) -> None:
        attach_calls.append(dict(kwargs))

    monkeypatch.setattr(
        portal_invocation_mod,
        "attach_oigb_relationship",
        attach_oigb_relationship,
    )

    result = await invoke_meta_portal_constructor(
        _request(
            index=index,
            invoke_function=invoke_function,
            target_class_config_id=target_class_config_id,
            source_oig_id=source_oig_id,
            source_branch_id=source_branch_id,
            target_object_id=target_object_id,
            commit=False,
        )
    )

    assert result.status == "succeeded"
    assert attach_calls == []


@pytest.mark.asyncio
async def test_committed_portal_constructor_fails_on_unexpected_target_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_class_config_id = uuid4()
    target_function_id = uuid4()
    index = _index(
        target_class_config_id=target_class_config_id,
        target_function_id=target_function_id,
    )
    source_oig_id = uuid4()
    source_branch_id = uuid4()
    target_object_id = uuid4()
    attach_calls: list[dict[str, object]] = []

    async def invoke_function(
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphCommitReceipt:
        return MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=uuid4(),
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

    async def attach_oigb_relationship(**kwargs: object) -> None:
        attach_calls.append(dict(kwargs))

    monkeypatch.setattr(
        portal_invocation_mod,
        "attach_oigb_relationship",
        attach_oigb_relationship,
    )

    result = await invoke_meta_portal_constructor(
        _request(
            index=index,
            invoke_function=invoke_function,
            target_class_config_id=target_class_config_id,
            source_oig_id=source_oig_id,
            source_branch_id=source_branch_id,
            target_object_id=target_object_id,
        )
    )

    assert result.status == "failed"
    assert result.error is not None
    assert "unexpected target branch" in result.error
    assert attach_calls == []
