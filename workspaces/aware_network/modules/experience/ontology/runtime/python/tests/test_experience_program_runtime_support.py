from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest

from ._experience_runtime_test_paths import REPO_ROOT

_REPO_ROOT = REPO_ROOT
for _path in (
    _REPO_ROOT / "apis" / "environment" / "python" / "aware_environment_service_dto",
    _REPO_ROOT / "libs" / "comms" / "python",
    _REPO_ROOT / "modules" / "experience" / "runtime",
    _REPO_ROOT / "modules" / "history" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "meta" / "runtime",
    _REPO_ROOT / "modules" / "meta" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "environment" / "runtime",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_environment_service_dto.environment.environment import (  # noqa: E402
    InvokeFunctionCallTarget,
    InvokeFunctionResponse,
)
from aware_experience.program import ontology_decode, runtime_support  # noqa: E402
from aware_meta_ontology.graph.config.object_config_graph_enums import (  # noqa: E402
    ObjectConfigGraphNodeType,
)
from aware_environment.branching import (  # noqa: E402
    stable_environment_thread_branch_id,
)


def test_experience_program_runtime_support_sources_are_clean() -> None:
    for relpath in (
        "workspaces/aware_network/modules/experience/ontology/runtime/python/aware_experience/program/runtime_support.py",
        "workspaces/aware_network/modules/experience/ontology/runtime/python/aware_experience/program/ontology_decode.py",
        "workspaces/aware_network/modules/experience/ontology/runtime/python/aware_experience/program/persistence.py",
        "workspaces/aware_network/modules/experience/ontology/runtime/python/aware_experience/program/lane_materialized_reader.py",
    ):
        source = (_REPO_ROOT / relpath).read_text()
        assert "aware_runtime" not in source


def test_program_stable_ids_preserve_runtime_formulas() -> None:
    environment_id = uuid4()
    thread_id = uuid4()

    assert runtime_support.stable_ids.stable_boot_process_id(
        environment_id=environment_id,
    ) == uuid5(NAMESPACE_URL, f"aware:process:{environment_id}:environment")
    assert runtime_support.stable_ids.stable_boot_thread_id(
        environment_id=environment_id,
    ) == uuid5(NAMESPACE_URL, f"aware:thread:{environment_id}:bootstrap")
    assert runtime_support.stable_ids.stable_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    ) == stable_environment_thread_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    )
    assert ontology_decode._resolve_decode_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
        request_branch_id=None,
    ) == stable_environment_thread_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    )


def _runtime_index_fixture() -> SimpleNamespace:
    function_id = uuid4()
    function_config = SimpleNamespace(id=function_id, name="set_running")
    function_link = SimpleNamespace(
        is_public=True,
        function_config=function_config,
        function_config_id=function_id,
    )
    class_config = SimpleNamespace(
        name="aware_experience_ontology.program.program.Program",
        class_config_function_configs=[function_link],
    )
    opg = SimpleNamespace(name="Program", projection_hash="hash:Program")
    ocg = SimpleNamespace(
        object_config_graph_nodes=[
            SimpleNamespace(
                type=ObjectConfigGraphNodeType.function,
                function_config=function_config,
                class_config=None,
            ),
            SimpleNamespace(
                type=ObjectConfigGraphNodeType.class_,
                function_config=None,
                class_config=class_config,
            ),
        ],
        object_projection_graphs=[opg],
    )
    return SimpleNamespace(
        function_id=function_id,
        index=SimpleNamespace(ocg=ocg),
    )


def test_program_ocg_support_resolves_projection_and_public_function() -> None:
    fixture = _runtime_index_fixture()
    index = cast(Any, fixture.index)

    assert (
        runtime_support.ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="Program",
        )
        == "hash:Program"
    )
    assert (
        runtime_support.ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix="Program",
            function_name="set_running",
        )
        == fixture.function_id
    )


@pytest.mark.asyncio
async def test_program_invoke_support_builds_environment_invoke_request() -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    branch_id = uuid4()
    object_id = uuid4()
    function_id = uuid4()
    captured: dict[str, object] = {}

    class _Invoker:
        async def invoke_function_with_index(
            self,
            *,
            index: object,
            request: object,
        ) -> InvokeFunctionResponse:
            captured["index"] = index
            captured["request"] = request
            return InvokeFunctionResponse(
                environment_id=environment_id,
                status="succeeded",
            )

    index = object()
    runtime = SimpleNamespace(invoker=_Invoker())

    response = (
        await runtime_support.invoke_support.invoke_instance_environment_function(
            runtime=runtime,
            index=cast(Any, index),
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash="hash:Program",
            object_id=object_id,
            function_id=function_id,
            args=["running"],
            commit=True,
        )
    )

    assert response.status == "succeeded"
    request = cast(Any, captured["request"])
    assert captured["index"] is index
    assert request.call_target == InvokeFunctionCallTarget.instance
    assert request.object_id == object_id
    assert request.function_id == function_id
    assert request.args == ["running"]
    assert request.commit is True
