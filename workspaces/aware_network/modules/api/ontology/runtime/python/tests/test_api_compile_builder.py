from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

import pytest

from _api_runtime_test_paths import (  # noqa: E402
    API_RUNTIME_ROOT,
    REPO_ROOT as _REPO_ROOT,
)

_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_API_RUNTIME_ROOT_STR = str(API_RUNTIME_ROOT)
if _API_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _API_RUNTIME_ROOT_STR)

from aware_api_runtime.ir import build_api_compile_plan  # noqa: E402
from aware_api_runtime.compile import compile_api_workspace  # noqa: E402
from aware_api_runtime.source.compiler import (
    load_api_ownership_from_sources,
)  # noqa: E402
from aware_api_runtime.ontology_graph.ontology import (
    build_api_ontology_plans,
)  # noqa: E402
from aware_api_runtime.models import ProjectionOwnedClassTruth  # noqa: E402
from api_runtime_fixture_artifacts import (  # noqa: E402
    write_home_api_dependency_runtime_artifacts,
)


def _write_home_devices_dependency_packages(root: Path) -> None:
    ontology_root = root / "modules" / "home" / "structure" / "ontology"
    (ontology_root / "aware" / "home").mkdir(parents=True, exist_ok=True)
    _ = (ontology_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_home"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home" / "home.aware").write_text(
        "\n".join(
            [
                "class Home {",
                "    name String key",
                "    doors Door[]",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home" / "door.aware").write_text(
        "\n".join(
            [
                "class Door {",
                "    label String",
                "    fn lock() -> Bool {",
                "    }",
                "    fn unlock() -> Bool {",
                "    }",
                "    fn open() -> Bool {",
                "    }",
                "    fn close() -> Bool {",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home_projection.aware").write_text(
        "\n".join(
            [
                "projection Home {",
                "    root home.Home",
                "    home.Home::doors",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    api_type_root = root / "apis" / "types" / "home"
    (api_type_root / "aware" / "door").mkdir(parents=True, exist_ok=True)
    _ = (api_type_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-api"',
                'fqn_prefix = "aware_home_api"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_home_api"',
                "",
                "[[dependencies]]",
                'package_name = "home-ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_home_api_dependency_runtime_artifacts(root)


def _write_home_devices_api_toml(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "home-devices-api"',
                'fqn_prefix = "aware_home_devices_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "home-api"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_home_devices_api_source(root: Path) -> Path:
    bindings = root / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    source_path = bindings / "home_devices.apis.aware"
    _ = source_path.write_text(
        "\n".join(
            [
                "api home_devices {",
                "    capability lock_door {",
                "        endpoint lock_door aware_home_api.door.LockDoor {",
                "            response aware_home_api.door.LockDoorResult;",
                "            function lock aware_home lock;",
                "        }",
                "    }",
                "    capability unlock_door {",
                "        endpoint unlock_door aware_home_api.door.UnlockDoor {",
                "            response aware_home_api.door.UnlockDoorResult;",
                "            function unlock aware_home unlock;",
                "        }",
                "    }",
                "    capability open_door {",
                "        endpoint open_door aware_home_api.door.DoorByLabel {",
                "            function open aware_home open;",
                "        }",
                "    }",
                "    capability close_door {",
                "        endpoint close_door aware_home_api.door.CloseDoor {",
                "            response aware_home_api.door.CloseDoorResult;",
                "            function close aware_home close;",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "        }",
                "        capability lock_door {",
                "            function lock aware_home.home.Door.lock;",
                "        }",
                "        capability unlock_door {",
                "            function unlock aware_home.home.Door.unlock;",
                "        }",
                "        capability open_door {",
                "            function open aware_home.home.Door.open;",
                "        }",
                "        capability close_door {",
                "            function close aware_home.home.Door.close;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return source_path


def test_load_api_ownership_valid(tmp_path: Path) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api home_public {",
                "    capability lock_door {",
                '        """Lock the front door."""',
                "        endpoint lock_door aware_home_api.door.LockDoor {",
                '            """Lock command."""',
                "            response aware_home_api.door.LockDoorResult;",
                "            stream server {",
                '                """Server push state."""',
                "                event snapshot aware_home_api.door.DoorSnapshot;",
                "                event delta aware_home_api.door.DoorDelta;",
                "            }",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "        }",
                "        capability lock_door {",
                "            function lock aware_home.home.Door.lock;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    projection_truth = {
        "aware_home.Home": {
            "Home": ProjectionOwnedClassTruth(
                class_fqn="aware_home_ontology.home.home.Home",
                attributes=frozenset({"doors"}),
                identity_key_attributes=frozenset({"name"}),
                relationship_targets=(("doors", "Door"),),
            ),
            "Door": ProjectionOwnedClassTruth(
                class_fqn="aware_home_ontology.home.home.Door",
                attributes=frozenset({"label", "is_locked"}),
                identity_key_attributes=frozenset({"label"}),
            ),
        }
    }

    ownership = load_api_ownership_from_sources(
        package_root=root,
        source_files=(Path("apis.aware"),),
        projection_truth_by_name=projection_truth,
    )

    assert len(ownership) == 1
    api = ownership[0]
    assert api.name == "home_public"
    assert len(api.capabilities) == 1
    assert api.capabilities[0].name == "lock_door"
    assert api.capabilities[0].description == "Lock the front door."
    assert len(api.capabilities[0].endpoints) == 1
    assert api.capabilities[0].endpoints[0].name == "lock_door"
    assert api.capabilities[0].endpoints[0].description == "Lock command."
    assert (
        api.capabilities[0].endpoints[0].request_config.class_ref
        == "aware_home_api.door.LockDoor"
    )
    assert api.capabilities[0].endpoints[0].request_config.response_config is not None
    assert (
        api.capabilities[0].endpoints[0].request_config.response_config.class_ref
        == "aware_home_api.door.LockDoorResult"
    )
    assert api.capabilities[0].endpoints[0].request_config.stream_config is not None
    assert (
        api.capabilities[0].endpoints[0].request_config.stream_config.stream_mode
        == "server"
    )
    assert (
        api.capabilities[0].endpoints[0].request_config.stream_config.description
        == "Server push state."
    )
    assert tuple(
        (event.kind, event.class_ref)
        for event in api.capabilities[0]
        .endpoints[0]
        .request_config.stream_config.event_configs
    ) == (
        ("delta", "aware_home_api.door.DoorDelta"),
        ("snapshot", "aware_home_api.door.DoorSnapshot"),
    )
    assert tuple(
        (
            function.name,
            function.graph_target,
            function.graph_capability_function_name,
        )
        for function in api.capabilities[0].endpoints[0].functions
    ) == (("lock", "aware_home", "lock"),)
    assert len(api.graphs) == 1
    graph = api.graphs[0]
    assert graph.target == "aware_home"
    assert len(graph.projections) == 1
    projection = graph.projections[0]
    assert projection.target == "aware_home.Home"
    assert len(graph.capabilities) == 1
    graph_capability = graph.capabilities[0]
    assert graph_capability.capability_name == "lock_door"
    assert len(graph_capability.functions) == 1
    assert graph_capability.functions[0].name == "lock"
    assert graph_capability.functions[0].target == "aware_home.home.Door.lock"


def test_load_api_ownership_allows_service_only_api_without_graph(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api agent {",
                "    capability subscribe_session {",
                "        endpoint subscribe_session aware_agent_service_dto.agent.session.service_operation.SubscribeAgentSessionRequest {",
                '            """Subscribe to one existing agent session."""',
                "            response aware_agent_service_dto.agent.session.service_operation.SubscribeAgentSessionResponse;",
                "            stream server {",
                '                """Canonical streamed session events."""',
                "                event snapshot aware_agent_service_dto.agent.session.event.AgentSessionStatusEvent;",
                "                event delta aware_agent_service_dto.agent.session.event.AgentSessionTurnEvent;",
                "                event error aware_agent_service_dto.agent.session.event.AgentSessionErrorEvent;",
                "                event complete aware_agent_service_dto.agent.session.event.AgentSessionCompleteEvent;",
                "            }",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ownership = load_api_ownership_from_sources(
        package_root=root,
        source_files=(Path("apis.aware"),),
        projection_truth_by_name=None,
        binding_truth_by_ref={},
    )

    assert len(ownership) == 1
    api = ownership[0]
    assert api.name == "agent"
    assert len(api.capabilities) == 1
    capability = api.capabilities[0]
    assert capability.name == "subscribe_session"
    assert len(capability.endpoints) == 1
    endpoint = capability.endpoints[0]
    assert endpoint.name == "subscribe_session"
    assert endpoint.functions == ()
    assert endpoint.request_config.class_ref == (
        "aware_agent_service_dto.agent.session.service_operation.SubscribeAgentSessionRequest"
    )
    assert endpoint.request_config.response_config is not None
    assert endpoint.request_config.response_config.class_ref == (
        "aware_agent_service_dto.agent.session.service_operation.SubscribeAgentSessionResponse"
    )
    assert endpoint.request_config.stream_config is not None
    assert endpoint.request_config.stream_config.stream_mode == "server"
    assert tuple(
        (event.kind, event.class_ref)
        for event in endpoint.request_config.stream_config.event_configs
    ) == (
        (
            "complete",
            "aware_agent_service_dto.agent.session.event.AgentSessionCompleteEvent",
        ),
        ("delta", "aware_agent_service_dto.agent.session.event.AgentSessionTurnEvent"),
        ("error", "aware_agent_service_dto.agent.session.event.AgentSessionErrorEvent"),
        (
            "snapshot",
            "aware_agent_service_dto.agent.session.event.AgentSessionStatusEvent",
        ),
    )
    assert api.graphs == ()


def test_load_api_ownership_allows_view_only_api(tmp_path: Path) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api meta_graph {",
                "    view graph_canvas on aware_meta.MetaGraph.graph state aware_meta_api.graph.MetaGraphCanvasViewState {",
                '        """Meta graph canvas state."""',
                "        stream snapshot",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ownership = load_api_ownership_from_sources(
        package_root=root,
        source_files=(Path("apis.aware"),),
        projection_truth_by_name=None,
        binding_truth_by_ref={},
    )

    assert len(ownership) == 1
    api = ownership[0]
    assert api.name == "meta_graph"
    assert api.capabilities == ()
    assert api.graphs == ()
    assert len(api.views) == 1
    view = api.views[0]
    assert view.name == "graph_canvas"
    assert view.observable_ref == "aware_meta.MetaGraph.graph"
    assert view.state_model_ref == "aware_meta_api.graph.MetaGraphCanvasViewState"
    assert view.view_ref == "meta_graph.graph_canvas"
    assert view.view_key == "graph_canvas"
    assert view.description == "Meta graph canvas state."
    assert view.stream_policy is not None
    assert view.stream_policy.stream_mode == "snapshot"


def test_load_api_ownership_lowers_view_capability_endpoint_binding(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api code {",
                "    view package_selector on CodePackage.codes state aware_code.CodePackageSelectorViewStateV1 {",
                "        stream snapshot",
                "        endpoint select_code view_action.select_code",
                "    }",
                "",
                "    capability view_action {",
                "        endpoint select_code aware_code.SelectCodeViewActionRequest {",
                "            response aware_code.SelectCodeViewActionResponse;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ownership = load_api_ownership_from_sources(
        package_root=root,
        source_files=(Path("apis.aware"),),
        projection_truth_by_name=None,
        binding_truth_by_ref={},
    )

    api = ownership[0]
    assert len(api.views) == 1
    view = api.views[0]
    assert [
        (binding.action_key, binding.endpoint_ref)
        for binding in view.capability_endpoints
    ] == [("select_code", "code.view_action.select_code")]
    plans = build_api_ontology_plans(api_ownership=ownership)
    assert [
        (
            row.view_name,
            row.action_key,
            row.endpoint_ref,
            row.capability_name,
            row.endpoint_name,
        )
        for row in plans[0].view_capability_endpoints
    ] == [
        (
            "package_selector",
            "select_code",
            "code.view_action.select_code",
            "view_action",
            "select_code",
        )
    ]


def test_load_api_ownership_rejects_view_capability_endpoint_api_prefix(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api code {",
                "    view package_selector on CodePackage.codes state aware_code.CodePackageSelectorViewStateV1 {",
                "        stream snapshot",
                "        endpoint select_code code.view_action.select_code",
                "    }",
                "",
                "    capability view_action {",
                "        endpoint select_code aware_code.SelectCodeViewActionRequest {",
                "            response aware_code.SelectCodeViewActionResponse;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"<capability>\.<endpoint>"):
        load_api_ownership_from_sources(
            package_root=root,
            source_files=(Path("apis.aware"),),
            projection_truth_by_name=None,
            binding_truth_by_ref={},
        )


def test_load_api_ownership_rejects_view_binding_without_endpoint(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api code {",
                "    view package_selector on CodePackage.codes state aware_code.CodePackageSelectorViewStateV1 {",
                "        endpoint select_code view_action.select_code",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown capability"):
        load_api_ownership_from_sources(
            package_root=root,
            source_files=(Path("apis.aware"),),
            projection_truth_by_name=None,
            binding_truth_by_ref={},
        )


def test_load_api_ownership_rejects_duplicate_view_endpoint_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api code {",
                "    view package_selector on CodePackage.codes state aware_code.CodePackageSelectorViewStateV1 {",
                "        endpoint select_code view_action.select_code",
                "        endpoint choose_code view_action.select_code",
                "    }",
                "",
                "    capability view_action {",
                "        endpoint select_code aware_code.SelectCodeViewActionRequest {",
                "            response aware_code.SelectCodeViewActionResponse",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate endpoint binding endpoint_ref"):
        load_api_ownership_from_sources(
            package_root=root,
            source_files=(Path("apis.aware"),),
            projection_truth_by_name=None,
            binding_truth_by_ref={},
        )


def test_load_api_ownership_allows_projection_only_graph_contract(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api attention {",
                "    capability watch_runtime_mount {",
                "        endpoint watch_runtime_mount aware_attention_api.attention.section.WatchAttentionRuntimeMountRequest {",
                "            response aware_attention_api.attention.section.WatchAttentionRuntimeMountResponse;",
                "        }",
                "    }",
                "",
                "    graph aware_attention {",
                "        projection aware_attention.FocusScope;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ownership = load_api_ownership_from_sources(
        package_root=root,
        source_files=(Path("apis.aware"),),
        projection_truth_by_name=None,
        binding_truth_by_ref={},
    )

    assert len(ownership) == 1
    api = ownership[0]
    assert api.name == "attention"
    assert len(api.graphs) == 1
    graph = api.graphs[0]
    assert graph.target == "aware_attention"
    assert len(graph.projections) == 1
    projection = graph.projections[0]
    assert projection.target == "aware_attention.FocusScope"


def test_load_api_ownership_rejects_projection_binding_in_api(tmp_path: Path) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api home_public {",
                "    capability lock_door {",
                "        endpoint lock_door aware_home_api.door.LockDoor",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "            binding aware_home_api.door_by_label Home::doors;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    try:
        _ = load_api_ownership_from_sources(
            package_root=root,
            source_files=(Path("apis.aware"),),
            projection_truth_by_name=None,
        )
    except ValueError as exc:
        assert "Projection node-key bindings are Experience-owned" in str(exc)
    else:
        raise AssertionError("Expected API compiler failure for API projection binding")


def test_load_api_ownership_rejects_legacy_capability_level_dto_syntax(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _ = (root / "apis.aware").write_text(
        "\n".join(
            [
                "api home_public {",
                "    capability lock_door aware_home_api.door.LockDoor;",
                "    graph aware_home {",
                "        capability lock_door {",
                "            function lock aware_home.home.Door.lock;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError, match="unknown capability|must include at least one capability"
    ):
        _ = load_api_ownership_from_sources(
            package_root=root,
            source_files=(Path("apis.aware"),),
            projection_truth_by_name=None,
        )


def test_home_story_api_lowers_graph_projection_and_capability_binding(
    tmp_path: Path,
) -> None:
    package_root = tmp_path
    _write_home_devices_dependency_packages(package_root)
    source_path = _write_home_devices_api_source(package_root)
    projection_truth = {
        "aware_home.Home": {
            "Home": ProjectionOwnedClassTruth(
                class_fqn="aware_home_ontology.home.home.Home",
                attributes=frozenset({"doors"}),
                identity_key_attributes=frozenset({"name"}),
                relationship_targets=(("doors", "Door"),),
            ),
            "Door": ProjectionOwnedClassTruth(
                class_fqn="aware_home_ontology.home.home.Door",
                attributes=frozenset({"label", "is_locked", "is_open"}),
                identity_key_attributes=frozenset({"label"}),
            ),
        }
    }

    ownership = load_api_ownership_from_sources(
        package_root=package_root,
        source_files=(source_path.relative_to(package_root),),
        projection_truth_by_name=projection_truth,
    )

    assert len(ownership) == 1
    api = ownership[0]
    assert api.name == "home_devices"
    assert len(api.capabilities) == 4
    capabilities_by_name = {
        capability.name: capability for capability in api.capabilities
    }
    assert tuple(sorted(capabilities_by_name)) == (
        "close_door",
        "lock_door",
        "open_door",
        "unlock_door",
    )
    assert (
        capabilities_by_name["lock_door"].endpoints[0].request_config.class_ref
        == "aware_home_api.door.LockDoor"
    )
    assert (
        capabilities_by_name["unlock_door"].endpoints[0].request_config.class_ref
        == "aware_home_api.door.UnlockDoor"
    )
    assert (
        capabilities_by_name["open_door"].endpoints[0].request_config.class_ref
        == "aware_home_api.door.DoorByLabel"
    )
    assert (
        capabilities_by_name["close_door"].endpoints[0].request_config.class_ref
        == "aware_home_api.door.CloseDoor"
    )
    assert tuple(
        (
            function.name,
            function.graph_target,
            function.graph_capability_function_name,
        )
        for function in capabilities_by_name["lock_door"].endpoints[0].functions
    ) == (("lock", "aware_home", "lock"),)
    assert tuple(
        function.name
        for function in capabilities_by_name["unlock_door"].endpoints[0].functions
    ) == ("unlock",)
    assert tuple(
        function.name
        for function in capabilities_by_name["open_door"].endpoints[0].functions
    ) == ("open",)
    assert tuple(
        function.name
        for function in capabilities_by_name["close_door"].endpoints[0].functions
    ) == ("close",)
    assert len(api.graphs) == 1
    graph = api.graphs[0]
    assert graph.target == "aware_home"
    assert len(graph.projections) == 1
    projection = graph.projections[0]
    assert projection.target == "aware_home.Home"
    graph_capabilities_by_name = {
        capability.capability_name: capability for capability in graph.capabilities
    }
    assert tuple(sorted(graph_capabilities_by_name)) == (
        "close_door",
        "lock_door",
        "open_door",
        "unlock_door",
    )
    assert tuple(
        (fn.name, fn.target) for fn in graph_capabilities_by_name["lock_door"].functions
    ) == (("lock", "aware_home.home.Door.lock"),)
    assert tuple(
        (fn.name, fn.target)
        for fn in graph_capabilities_by_name["unlock_door"].functions
    ) == (("unlock", "aware_home.home.Door.unlock"),)
    assert tuple(
        (fn.name, fn.target) for fn in graph_capabilities_by_name["open_door"].functions
    ) == (("open", "aware_home.home.Door.open"),)
    assert tuple(
        (fn.name, fn.target)
        for fn in graph_capabilities_by_name["close_door"].functions
    ) == (("close", "aware_home.home.Door.close"),)


def test_home_story_api_compile_plan_binds_request_class_config_ids(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    package_root = tmp_path
    _write_home_devices_dependency_packages(package_root)
    toml_path = _write_home_devices_api_toml(package_root)
    _write_home_devices_api_source(package_root)
    compile_result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=workspace_root,
    )
    plan = build_api_compile_plan(
        snapshot=compile_result.snapshot,
        projection_truth_by_name={
            "aware_home.Home": {
                "Home": ProjectionOwnedClassTruth(
                    class_fqn="aware_home_ontology.home.home.Home",
                    attributes=frozenset({"doors"}),
                    identity_key_attributes=frozenset({"name"}),
                    relationship_targets=(("doors", "Door"),),
                ),
                "Door": ProjectionOwnedClassTruth(
                    class_fqn="aware_home_ontology.home.home.Door",
                    attributes=frozenset({"label", "is_locked", "is_open"}),
                    identity_key_attributes=frozenset({"label"}),
                ),
            }
        },
    )

    capabilities_by_name = {
        capability.name: capability for capability in plan.api_ownership[0].capabilities
    }
    request_config = capabilities_by_name["open_door"].endpoints[0].request_config
    assert request_config.class_ref == "aware_home_api.door.DoorByLabel"
    assert request_config.class_config_id is not None


def test_api_compile_plan_binds_view_state_model_class_config_ids(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _ = (root / "aware.api.toml").write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "meta-graph-api"',
                'fqn_prefix = "aware_meta_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    bindings = root / "bindings"
    bindings.mkdir(parents=True)
    _ = (bindings / "meta_graph.apis.aware").write_text(
        "\n".join(
            [
                "api meta_graph {",
                "    view graph_canvas on aware_meta.MetaGraph.graph state aware_meta_api.graph.MetaGraphCanvasViewState {",
                "        stream snapshot",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    state_model_id = uuid4()

    compile_result = compile_api_workspace(
        toml_path=root / "aware.api.toml",
        repo_root=root,
    )
    plan = build_api_compile_plan(
        snapshot=compile_result.snapshot,
        dependency_class_config_ids={
            "aware_meta_api.graph.MetaGraphCanvasViewState": state_model_id,
        },
    )

    view = plan.api_ownership[0].views[0]
    assert view.state_model_id == state_model_id
    ontology_view = plan.api_ontology[0].views[0]
    assert ontology_view.state_model_ref == (
        "aware_meta_api.graph.MetaGraphCanvasViewState"
    )
    assert ontology_view.state_model_id == state_model_id
    assert plan.api_ontology[0].view_stream_policies[0].stream_mode == "snapshot"
