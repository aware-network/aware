from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from ._experience_runtime_test_paths import EXPERIENCE_ONTOLOGY_RUNTIME_ROOT, REPO_ROOT

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
from aware_experience.environment_profile import runtime_support  # noqa: E402
from aware_meta_ontology.graph.config.object_config_graph_enums import (  # noqa: E402
    ObjectConfigGraphNodeType,
)
from aware_environment.branching import (  # noqa: E402
    stable_environment_thread_branch_id,
)


def test_environment_profile_runtime_support_sources_are_clean() -> None:
    support_source = (
        EXPERIENCE_ONTOLOGY_RUNTIME_ROOT
        / "aware_experience"
        / "environment_profile"
        / "runtime_support.py"
    ).read_text()
    materialization_source = (
        EXPERIENCE_ONTOLOGY_RUNTIME_ROOT
        / "aware_experience"
        / "environment_profile"
        / "materialization_runtime.py"
    ).read_text()

    assert "aware_runtime" not in support_source
    assert "aware_runtime" not in materialization_source


def test_stable_ids_preserve_environment_profile_formulas() -> None:
    environment_id = uuid4()
    thread_id = uuid4()
    process_id = uuid4()
    opgi_id = uuid4()

    assert runtime_support.stable_ids.stable_boot_process_id(
        environment_id=environment_id
    ) == uuid5(NAMESPACE_URL, f"aware:process:{environment_id}:environment")
    assert runtime_support.stable_ids.stable_boot_thread_id(
        environment_id=environment_id
    ) == uuid5(NAMESPACE_URL, f"aware:thread:{environment_id}:bootstrap")
    assert runtime_support.stable_ids.stable_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    ) == stable_environment_thread_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    )
    assert runtime_support.stable_ids.stable_process_config_id_for_process(
        process_id=process_id,
    ) == uuid5(NAMESPACE_URL, f"aware:process_config:{process_id}")
    assert runtime_support.stable_ids.stable_thread_config_projection_assoc_id(
        thread_config_id=thread_id,
        object_projection_graph_identity_id=opgi_id,
    ) == uuid5(
        NAMESPACE_URL,
        f"aware:thread_config_opgi_assoc:{thread_id}:{opgi_id}",
    )


def _runtime_index_fixture() -> SimpleNamespace:
    class_id = uuid4()
    attr_id = uuid4()
    function_id = uuid4()
    link_id = uuid4()
    opg_id = uuid4()

    function_config = SimpleNamespace(id=function_id, name="build")
    function_link = SimpleNamespace(
        id=link_id,
        is_public=True,
        function_config=function_config,
        function_config_id=function_id,
    )
    class_config = SimpleNamespace(
        id=class_id,
        name="aware_example.Profile",
        class_config_function_configs=[function_link],
        class_config_attribute_configs=[
            SimpleNamespace(
                attribute_config=SimpleNamespace(id=attr_id, name="title"),
            )
        ],
    )
    opg = SimpleNamespace(
        id=opg_id,
        name="EnvironmentExperience",
        projection_hash="hash:EnvironmentExperience",
        object_projection_graph_constructors=[
            SimpleNamespace(function_constructor_id=link_id)
        ],
    )
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
        attr_id=attr_id,
        class_id=class_id,
        function_id=function_id,
        opg_id=opg_id,
        index=SimpleNamespace(
            ocg=ocg,
            opg_by_hash={opg.projection_hash: opg},
        ),
    )


def test_ocg_support_resolves_projection_function_class_and_attributes() -> None:
    fixture = _runtime_index_fixture()
    index = cast(Any, fixture.index)

    assert (
        runtime_support.ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="EnvironmentExperience",
        )
        == "hash:EnvironmentExperience"
    )
    assert (
        runtime_support.ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix="Profile",
            function_name="build",
        )
        == fixture.function_id
    )
    assert (
        runtime_support.ocg_support.resolve_class_config_id(
            index=index,
            class_name_suffix="aware_example.Profile",
        )
        == fixture.class_id
    )
    assert runtime_support.ocg_support.build_attr_name_by_id_for_class_config(
        index=index,
        class_config_id=fixture.class_id,
    ) == {fixture.attr_id: "title"}
    assert (
        runtime_support.ocg_support.resolve_single_opg_constructor_function_id(
            index=index,
            object_projection_graph_id=fixture.opg_id,
        )
        == fixture.function_id
    )


def test_ocg_support_builds_opgi_index(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = _runtime_index_fixture()
    opgi_id = uuid4()

    def _fake_resolve_meta_graph_ocgi_opgi(
        *,
        index: object,
        projection_hash: str,
    ) -> tuple[None, object]:
        _ = index, projection_hash
        return None, SimpleNamespace(
            id=opgi_id,
            projection_name="EnvironmentExperience",
            object_projection_graph_observables=[
                SimpleNamespace(observable_key="detail", key="fallback"),
                SimpleNamespace(observable_key="", key="summary"),
            ],
        )

    monkeypatch.setattr(
        runtime_support,
        "resolve_meta_graph_ocgi_opgi",
        _fake_resolve_meta_graph_ocgi_opgi,
    )

    assert runtime_support.ocg_support.build_opgi_index(
        index=cast(Any, fixture.index),
    ) == {"EnvironmentExperience": (opgi_id, {"detail"})}


def test_oig_support_extracts_scalar_json_and_attributes() -> None:
    title_attr_id = uuid4()
    payload_attr_id = uuid4()
    class_instance = SimpleNamespace(
        attributes=[
            SimpleNamespace(
                attribute_config_id=title_attr_id,
                value_root=SimpleNamespace(primitive_value={"value": "Dashboard"}),
            ),
            SimpleNamespace(
                attribute_config_id=payload_attr_id,
                value_root=SimpleNamespace(
                    child_links=[
                        SimpleNamespace(
                            role="key",
                            identity_key="name",
                            child=SimpleNamespace(primitive_value={"value": "mode"}),
                        ),
                        SimpleNamespace(
                            role="value",
                            identity_key="name",
                            child=SimpleNamespace(primitive_value={"value": "live"}),
                        ),
                    ]
                ),
            ),
        ]
    )

    assert (
        runtime_support.oig_support.extract_attr_scalar(
            class_instance=class_instance,
            attr_name_by_id={title_attr_id: "title"},
            name="title",
        )
        == "Dashboard"
    )
    assert runtime_support.oig_support.extract_attr_json(
        class_instance=class_instance,
        attr_name_by_id={payload_attr_id: "payload"},
        name="payload",
    ) == {"mode": "live"}


@pytest.mark.asyncio
async def test_lane_support_materializes_source_object_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _runtime_index_fixture()
    branch_id = uuid4()
    commit_id = uuid4()
    oig_id = uuid4()
    source_object_id = uuid4()

    class _Store:
        async def head(
            self, *, branch_id: UUID, projection_hash: str
        ) -> dict[str, str]:
            _ = branch_id, projection_hash
            return {
                "commit_id": str(commit_id),
                "object_instance_graph_id": str(oig_id),
            }

    class _Materializer:
        async def get(self, **kwargs: object) -> tuple[object, object]:
            assert kwargs["branch_id"] == branch_id
            assert kwargs["commit_id"] == commit_id
            assert kwargs["oig_id"] == oig_id
            return (
                SimpleNamespace(
                    class_instances=[
                        SimpleNamespace(source_object_id=source_object_id),
                    ]
                ),
                object(),
            )

    monkeypatch.setattr(runtime_support, "FSCommitStore", _Store)
    monkeypatch.setattr(runtime_support, "CachedLaneMaterializer", _Materializer)

    assert await runtime_support.lane_support.materialize_lane_instance_ids(
        index=cast(Any, fixture.index),
        branch_id=branch_id,
        projection_hash="hash:EnvironmentExperience",
    ) == {source_object_id}


@pytest.mark.asyncio
async def test_invoke_support_builds_environment_invoke_request() -> None:
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
            projection_hash="hash:Environment",
            object_id=object_id,
            function_id=function_id,
            args=["hello"],
            commit=True,
        )
    )

    assert response.status == "succeeded"
    request = cast(Any, captured["request"])
    assert captured["index"] is index
    assert request.call_target == InvokeFunctionCallTarget.instance
    assert request.object_id == object_id
    assert request.function_id == function_id
    assert request.args == ["hello"]
    assert request.commit is True
